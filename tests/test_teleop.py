from __future__ import annotations

import argparse
import signal
import sys
from dataclasses import dataclass
from time import monotonic, sleep

from carbot.config.loader import load_run_config
from carbot.factories.app_factory import build_app

from carbot.control.commands import MotorCommand, ServoCommand
from carbot.control.loop import ControlLoop, ControlLoopConfig
from carbot.control.mux import PriorityMux, SourceEntry
from carbot.inputs.keyboard_teleop import KeyboardTeleop, KeyboardTeleopConfig


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="teleop_test")
    p.add_argument("--hz", type=float, default=50.0)
    p.add_argument("--status-hz", type=float, default=2.0)
    p.add_argument("--no-status", action="store_true")
    p.add_argument("--debug-keys", action="store_true")
    return p.parse_args()


def _install_sigterm_exit() -> None:
    def _on_sigterm(_signum, _frame) -> None:
        raise SystemExit(143)

    signal.signal(signal.SIGTERM, _on_sigterm)


@dataclass(frozen=True, slots=True)
class ServoSource:
    teleop: KeyboardTeleop

    def latest(self) -> ServoCommand | None:
        return self.teleop.latest_servo()


def _print_controls() -> None:
    print(
        "\n=== TELEOP CONTROLS ===\n"
        "Motor:\n"
        "  ↑ / ↓ = forward / backward\n"
        "  ← / → = in-place left / right\n"
        "  u/o = forward-left / forward-right arc\n"
        "  j/l = backward-left / backward-right arc\n"
        "  space = motor stop\n"
        "\nServo:\n"
        "  a/d = pan left/right\n"
        "  w/s = tilt up/down\n"
        "  c = center (pan=0, tilt=0)\n"
        "\nQuit:\n"
        "  q = quit\n"
        "  Ctrl+C = quit (handled in raw mode)\n"
        "\nNote: terminal is in RAW mode while running (no echo). That’s normal.\n"
    )
    sys.stdout.flush()


def main() -> int:
    args = parse_args()
    _install_sigterm_exit()

    if not sys.stdin.isatty():
        raise RuntimeError(
            "stdin is not a TTY. Keyboard teleop needs an interactive terminal."
        )

    cfg = load_run_config(args.config)
    app = build_app(cfg)

    if app.motor is None and app.servo is None:
        raise RuntimeError("Neither motor nor servo is configured in this run config.")

    _print_controls()

    teleop = KeyboardTeleop(
        KeyboardTeleopConfig(debug_keys=bool(args.debug_keys))
    )
    teleop.start()

    motor_mux = PriorityMux[MotorCommand](
        [SourceEntry(source=teleop, max_age_s=0.25, priority=0, name="kb")]
    )
    servo_mux = PriorityMux[ServoCommand](
        [SourceEntry(source=ServoSource(teleop), max_age_s=60.0, priority=0, name="kb")]
    )

    loop = ControlLoop(
        cfg=ControlLoopConfig(hz=float(args.hz)),
        motor=app.motor,
        servo=app.servo,
        motor_mux=motor_mux if app.motor is not None else None,
        servo_mux=servo_mux if app.servo is not None else None,
    )

    tick_dt = 1.0 / float(args.hz) if args.hz > 0 else 0.02
    status_dt = 1.0 / float(args.status_hz) if args.status_hz > 0 else 0.5
    next_status_t = monotonic() + status_dt

    try:
        while not teleop.quit_requested:
            err = teleop.thread_error()
            if err is not None:
                raise RuntimeError(f"KeyboardTeleop thread crashed: {err!r}") from err

            loop.tick()
            sleep(tick_dt)

            if not args.no_status and monotonic() >= next_status_t:
                m = teleop.latest_motor()
                s = teleop.latest_servo()

                m_str = (
                    "None"
                    if m is None
                    else f"throttle={m.throttle} steer={m.steer_differential}"
                )
                s_str = "None" if s is None else f"pan={s.pan} tilt={s.tilt}"

                if args.debug_keys:
                    k, b, t = teleop.debug_last_key()
                    print(
                        f"[teleop] motor={m_str} | servo={s_str} | "
                        f"last_key={k!r} last_bytes={b!r} last_read_t={t:.6f}"
                    )
                else:
                    print(f"[teleop] motor={m_str} | servo={s_str}")

                sys.stdout.flush()
                next_status_t = monotonic() + status_dt

        return 0

    except KeyboardInterrupt:
        return 130
    except SystemExit as e:
        return int(e.code) if isinstance(e.code, int) else 143
    finally:
        try:
            teleop.close()
        finally:
            app.close()


if __name__ == "__main__":
    raise SystemExit(main())