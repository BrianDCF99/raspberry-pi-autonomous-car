from __future__ import annotations

import argparse
from time import sleep
from typing import Callable

from carbot.config.loader import load_run_config
from carbot.factories.app_factory import build_app


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="servo_test")
    return p.parse_args()


def sweep(
    move_fn: Callable[[int], None],
    start: int,
    end: int,
    step: int,
    delay: float = 0.005,
) -> None:
    if step <= 0:
        raise ValueError("step must be > 0")

    step = step if end >= start else -step
    stop = end + (1 if step > 0 else -1)

    for angle in range(start, stop, step):
        move_fn(angle)
        sleep(delay)


def main() -> int:
    args = parse_args()

    cfg = load_run_config(args.config)
    app = build_app(cfg)

    assert app.servo is not None

    assert app.motor is None
    assert app.infrared is None
    assert app.ultrasonic is None
    assert app.camera is None
    assert app.streaming is None

    driver = app.servo
    try:
        for _ in range(3):
            sweep(driver.set_pan, 0, 60, step=1)
            sweep(driver.set_pan, 60, -60, step=1)
            sweep(driver.set_pan, -60, 0, step=1)

            sweep(driver.set_tilt, 0, -10, step=1)
            sweep(driver.set_tilt, -10, 45, step=1)
            sweep(driver.set_tilt, 45, 0, step=1)

        # driver.set_tilt(80)
        # driver.set_pan(30)
        # sleep(90)

        # driver.set_tilt(80)
        # driver.set_pan(160)
        # sleep(90)

        return 0
    except KeyboardInterrupt:
        return 130

    finally:
        if driver is not None:
            driver.close()


if __name__ == "__main__":
    raise SystemExit(main())
