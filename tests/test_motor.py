from __future__ import annotations

import argparse
from collections.abc import Callable
from time import sleep

from carbot.config.loader import load_motor_config
from carbot.contracts.motor_controller import MotorController
from carbot.controllers.fake.motor_controller import FakeMotorController
from carbot.controllers.freenove.motor_controller import FreenoveMotorController
from carbot.drivers.motor_driver import MotorDriver

CONTROLLERS: dict[str, Callable[[], MotorController]] = {
    "test": FakeMotorController,
    "freenove": FreenoveMotorController,
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--controller", choices=sorted(CONTROLLERS), default="test")
    p.add_argument("--car-cfg", default="slow_car")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    motor_ctl = CONTROLLERS[args.controller]()
    motor_cfg = load_motor_config(args.car_cfg)

    driver = MotorDriver(motor_ctl, motor_cfg)

    try:
        # forward
        driver.drive(1500, 0)
        sleep(1)

        # backward
        driver.drive(-1500, 0)
        sleep(1)

        # in-place right
        driver.drive(0, 1500)
        sleep(1)

        # in-place left
        driver.drive(0, -1500)
        sleep(1)

        # forward-right arc
        driver.drive(1500, 1500)
        sleep(1)

        # backward-right arc
        driver.drive(-1500, -1500)
        sleep(1)

        # forward-left arc
        driver.drive(1500, -1500)
        sleep(1)

        # backward-left arc
        driver.drive(-1500, 1500)
        sleep(1)
        return 0

    except KeyboardInterrupt:
        return 130

    finally:
        if driver is not None:
            driver.close()


if __name__ == "__main__":
    raise SystemExit(main())
