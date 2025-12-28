from __future__ import annotations

import argparse
import os
import signal
import sys
import termios
import tty
from select import select
from time import monotonic, sleep
from typing import Callable

import fcntl

from carbot.config.loader import load_run_config
from carbot.factories.app_factory import build_app


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="motor_test")
    p.add_argument("--speed", type=int, default=1500)      # throttle magnitude
    p.add_argument("--turn", type=int, default=1500)       # yaw magnitude
    p.add_argument("--deadman", type=float, default=0.15)  # seconds no input -> stop
    p.add_argument("--poll", type=float, default=0.02)     # select poll interval
    return p.parse_args()


def _install_sigterm_exit() -> None:
    def _on_sigterm(_signum, _frame) -> None:
        raise SystemExit(143)

    signal.signal(signal.SIGTERM, _on_sigterm)


class _RawNonBlockingStdin:
    def __init__(self) -> None:
        self._fd = sys.stdin.fileno()
        self._old_term = None
        self._old_flags = None

    def __enter__(self) -> int:
        self._old_term = termios.tcgetattr(self._fd)
        self._old_flags = fcntl.fcntl(self._fd, fcntl.F_GETFL)

        tty.setraw(self._fd)
        fcntl.fcntl(self._fd, fcntl.F_SETFL, self._old_flags | os.O_NONBLOCK)
        return self._fd

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._old_term is not None:
            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._old_term)
        if self._old_flags is not None:
            fcntl.fcntl(self._fd, fcntl.F_SETFL, self._old_flags)


def _read_available(fd: int, *, timeout: float) -> bytes:
    r, _, _ = select([fd], [], [], timeout)
    if not r:
        return b""
    try:
        return os.read(fd, 64)
    except BlockingIOError:
        return b""


def _pop_key(buf: str) -> tuple[str | None, str]:
    if not buf:
        return None, buf

    # Arrow keys: ESC [ A/B/C/D
    if buf[0] == "\x1b":
        if len(buf) < 3:
            return None, buf
        if buf[1] == "[" and buf[2] in ("A", "B", "C", "D"):
            return buf[:3], buf[3:]
        return "\x1b", buf[1:]

    return buf[0], buf[1:]


class MotorActions:
    def __init__(self, motor, *, speed: int, turn: int) -> None:
        self._motor = motor
        self._speed = int(speed)
        self._turn = int(turn)

    # --- primitives ---
    def stop(self) -> None:
        self._motor.drive(0, 0)

    # forward/back
    def forward(self) -> None:
        self._motor.drive(self._speed, 0)

    def backward(self) -> None:
        self._motor.drive(-self._speed, 0)

    # in-place turning
    def in_place_right(self) -> None:
        self._motor.drive(0, -self._turn)

    def in_place_left(self) -> None:
        self._motor.drive(0, self._turn)

    def forward_right_arc(self) -> None:
        self._motor.drive(self._speed, -self._turn)

    def forward_left_arc(self) -> None:
        self._motor.drive(self._speed, self._turn)

    def backward_right_arc(self) -> None:
        self._motor.drive(-self._speed, self._turn)

    def backward_left_arc(self) -> None:
        self._motor.drive(-self._speed, -self._turn)


def main() -> int:
    args = parse_args()
    cfg = load_run_config(args.config)
    app = build_app(cfg)

    _install_sigterm_exit()

    motor = app.motor
    if motor is None:
        raise RuntimeError("Motor driver is not configured (app.motor is None)")

    actions = MotorActions(motor, speed=args.speed, turn=args.turn)

    deadman_s = float(args.deadman)
    poll_s = float(args.poll)

    keymap: dict[str, Callable[[], None]] = {
        "\x1b[A": actions.forward,           # ↑
        "\x1b[B": actions.backward,          # ↓
        "\x1b[C": actions.in_place_right,    # →
        "\x1b[D": actions.in_place_left,     # ←
        "u": actions.forward_left_arc,       # diagonal
        "o": actions.forward_right_arc,
        "j": actions.backward_left_arc,
        "l": actions.backward_right_arc,
        " ": actions.stop,
    }

    print(
        "Keyboard motor control (hold-to-move):\n"
        "  ↑ / ↓ = forward / backward\n"
        "  ← / → = in-place left / in-place right\n"
        "  u/o = forward-left / forward-right arc\n"
        "  j/l = backward-left / backward-right arc\n"
        "  space = stop\n"
        "  q = quit\n"
    )

    last_input_t = monotonic()
    moving = False
    buf = ""

    def run_action(fn: Callable[[], None]) -> None:
        nonlocal moving
        fn()
        moving = fn is not actions.stop
        last_input_t = monotonic()  # (shadowed below on purpose)

    try:
        actions.stop()

        with _RawNonBlockingStdin() as fd:
            while True:
                data = _read_available(fd, timeout=poll_s)
                if data:
                    buf += data.decode("utf-8", errors="ignore")
                    last_input_t = monotonic()

                while True:
                    k, buf = _pop_key(buf)
                    if k is None:
                        break

                    if k == "q":
                        return 0

                    fn = keymap.get(k)
                    if fn is None:
                        continue

                    fn()
                    moving = fn is not actions.stop
                    last_input_t = monotonic()

                if moving and (monotonic() - last_input_t) >= deadman_s:
                    actions.stop()
                    moving = False

    except KeyboardInterrupt:
        return 130
    except SystemExit as e:
        return int(e.code) if isinstance(e.code, int) else 143
    finally:
        try:
            actions.stop()
            sleep(0.05)
        finally:
            app.close()


if __name__ == "__main__":
    raise SystemExit(main())