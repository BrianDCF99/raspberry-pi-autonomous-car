from __future__ import annotations

import argparse
from time import sleep

from carbot.config.loader import load_run_config
from carbot.factories.app_factory import build_app


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="motor_test")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    cfg = load_run_config(args.config)
    app = build_app(cfg)

    assert app.motor is not None

    assert app.servo is None
    assert app.infrared is None
    assert app.ultrasonic is None
    assert app.camera is None
    assert app.streaming is None

    try:
        # forward
        app.motor.drive(1500, 0)
        sleep(1)

        # backward
        app.motor.drive(-1500, 0)
        sleep(1)

        # in-place right
        app.motor.drive(0, 1500)
        sleep(1)

        # in-place left
        app.motor.drive(0, -1500)
        sleep(1)

        # forward-right arc
        app.motor.drive(1500, 1500)
        sleep(1)

        # backward-right arc
        app.motor.drive(-1500, -1500)
        sleep(1)

        # forward-left arc
        app.motor.drive(1500, -1500)
        sleep(1)

        # backward-left arc
        app.motor.drive(-1500, 1500)
        sleep(1)
        return 0

    except KeyboardInterrupt:
        return 130

    finally:
        if app.motor is not None:
            app.motor.close()


if __name__ == "__main__":
    raise SystemExit(main())
