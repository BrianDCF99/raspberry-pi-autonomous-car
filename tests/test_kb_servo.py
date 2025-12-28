from __future__ import annotations

import argparse
import os
import signal
import sys
import termios
import tty
from select import select
from time import sleep

import fcntl

from carbot.config.loader import load_run_config
from carbot.factories.app_factory import build_app


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="servo_test")
    p.add_argument("--step", type=int, default=5)       # delta per key repeat
    p.add_argument("--poll", type=float, default=0.01)   # select() poll interval
    p.add_argument("--invert-pan", action="store_true")
    p.add_argument("--invert-tilt", action="store_true")
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


def main() -> int:
    args = parse_args()
    cfg = load_run_config(args.config)
    app = build_app(cfg)

    _install_sigterm_exit()

    servo = app.servo
    if servo is None:
        raise RuntimeError("Servo driver is not configured (app.servo is None)")

    step = int(args.step)
    pan_sign = -1 if args.invert_pan else 1
    tilt_sign = -1 if args.invert_tilt else 1
    poll_s = float(args.poll)

    print(
        "Keyboard servo control:\n"
        "  a/d = pan left/right\n"
        "  w/s = tilt up/down\n"
        "  c = center\n"
        "  space = center\n"
        "  q = quit\n"
        "  (use --invert-pan / --invert-tilt if directions are backwards)\n"
    )

    def pan_delta(delta: int) -> None:
        servo.set_pan(servo.curr_pan_angle + delta)

    def tilt_delta(delta: int) -> None:
        servo.set_tilt(servo.curr_tilt_angle + delta)

    buf = ""

    try:
        with _RawNonBlockingStdin() as fd:
            while True:
                data = _read_available(fd, timeout=poll_s)
                if data:
                    buf += data.decode("utf-8", errors="ignore")

                while buf:
                    k = buf[0]
                    buf = buf[1:]

                    if k == "q":
                        return 0

                    if k == "c" or k == " ":
                        servo.center()
                        continue

                    if k == "a":
                        pan_delta(-step * pan_sign)
                        continue

                    if k == "d":
                        pan_delta(step * pan_sign)
                        continue

                    if k == "w":
                        tilt_delta(step * tilt_sign)
                        continue

                    if k == "s":
                        tilt_delta(-step * tilt_sign)
                        continue

    except KeyboardInterrupt:
        return 130
    except SystemExit as e:
        return int(e.code) if isinstance(e.code, int) else 143
    finally:
        try:
            servo.center()
            sleep(0.05)
        finally:
            app.close()


if __name__ == "__main__":
    raise SystemExit(main())