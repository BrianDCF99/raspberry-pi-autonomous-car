from __future__ import annotations

import argparse
import signal
import sys
import threading
from typing import cast

from time import monotonic, sleep

from carbot.config.loader import load_run_config
from carbot.control.commands import MotorCommand, ServoCommand
from carbot.control.loop import ControlLoop, ControlLoopConfig, MotorSink, ServoSink
from carbot.control.mux import PriorityMux, SourceEntry
from carbot.factories.app_factory import build_app, App
from carbot.inputs.keyboard_teleop import KeyboardTeleop, MotorSource, ServoSource


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="full")
    p.add_argument("--hz", type=float, default=50.0)
    p.add_argument("--status-hz", type=float, default=2.0)
    p.add_argument("--no-status", action="store_true")
    p.add_argument("--debug-keys", action="store_true")
    return p.parse_args()


def _install_sigterm_exit() -> None:
    def _on_sigterm(_signum, _frame) -> None:
        raise SystemExit(143)

    signal.signal(signal.SIGTERM, _on_sigterm)


def make_kb_muxs(
    app: App,
    max_age: float,
) -> tuple[PriorityMux[MotorCommand] | None, PriorityMux[ServoCommand] | None]:
    if app.teleop is None:
        raise RuntimeError(
            "app.teleop is None. Run config must set 'teleop_cfg' (and optionally 'keyboard')."
        )

    if not isinstance(app.teleop, KeyboardTeleop):
        raise RuntimeError(
            f"make_kb_muxs requires KeyboardTeleop, got {type(app.teleop).__name__}"
        )
    kb_teleop = app.teleop
    
    m_mux = (
        PriorityMux[MotorCommand](
            [
                SourceEntry(
                    source=MotorSource(kb_teleop),
                    max_age_s=max_age,
                    priority=0,
                    name="kb",
                )
            ]
        )
        if getattr(app, "motor", None) is not None
        else None
    )

    s_mux = (
        PriorityMux[ServoCommand](
            [
                SourceEntry(
                    source=ServoSource(kb_teleop),
                    max_age_s=max_age,
                    priority=0,
                    name="kb",
                )
            ]
        )
        if getattr(app, "servo", None) is not None
        else None
    )

    return m_mux, s_mux


def make_control_loop(
    hz: float,
    motor: MotorSink | None,
    servo: ServoSink | None,
    motor_mux: PriorityMux[MotorCommand] | None,
    servo_mux: PriorityMux[ServoCommand] | None,
) -> ControlLoop:
    return ControlLoop(
        cfg=ControlLoopConfig(hz=float(hz)),
        motor=motor,
        servo=servo,
        motor_mux=motor_mux,
        servo_mux=servo_mux,
    )


def run() -> int:
    args = parse_args()
    _install_sigterm_exit()

    cfg = load_run_config(args.config)
    app = build_app(cfg)

    try:
        teleop = getattr(app, "teleop", None)
        if teleop is None:
            raise RuntimeError(
                "app.teleop is None. Run config must set 'teleop_cfg' (and optionally 'keyboard')."
            )

        # best-effort: allow CLI override if the cfg supports it
        if hasattr(teleop, "cfg") and hasattr(teleop.cfg, "debug_keys"):
            teleop.cfg.debug_keys = bool(args.debug_keys)

        print(teleop.help_text(teleop_cfg_name=cfg.teleop_cfg))
        sys.stdout.flush()

        teleop.start()

        max_age = max(0.05, float(teleop.cfg.deadman_s) * 2.0)
        motor_mux, servo_mux = make_kb_muxs(app=app, max_age=max_age)

        loop = make_control_loop(
            args.hz,
            getattr(app, "motor", None),
            getattr(app, "servo", None),
            motor_mux,
            servo_mux,
        )

        tick_dt = 1.0 / float(args.hz) if args.hz > 0 else 0.02
        status_dt = 1.0 / float(args.status_hz) if args.status_hz > 0 else 0.5
        next_status_t = monotonic() + status_dt

        # Streaming (run in background so teleop/control loop can run)
        streaming = getattr(app, "streaming", None)
        if streaming is None:
            raise RuntimeError(
                "app.streaming is None. Your run config must set 'networking' and also configure camera_* "
                "(camera_controller + camera_cfg + camera_policy)."
            )

        # Camera (if present)
        camera = getattr(app, "camera", None)
        if camera is not None:
            cam_t = threading.Thread(target=camera.start, name="camera-start", daemon=True)
            cam_t.start()

        stream_t = threading.Thread(
            target=streaming.serve_forever,
            name="streaming",
            daemon=True,
        )
        stream_t.start()

        # Teleop + control loop
        while not teleop.quit_requested:
            err = teleop.thread_error()
            if err is not None:
                raise RuntimeError(f"Teleop thread crash: {err!r}") from err

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

                if getattr(teleop.cfg, "debug_keys", False):
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
        app.close()


if __name__ == "__main__":
    raise SystemExit(run())