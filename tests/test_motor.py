from __future__ import annotations

from time import sleep
import argparse

from carbot.contracts.motor_controller import MotorController
from carbot.controllers.fake.motor_controller import FakeMotorController
from carbot.controllers.freenove.motor_controller import FreenoveMotorController
from carbot.config.loader import load_motor_config
from carbot.drivers.motor_driver import MotorDriver



def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--hardware", choices=["test", "pi"], default="test")
    p.add_argument("--car-cfg", default="slow_car")
    return p.parse_args()

def build_motor_controller( device: str ) -> MotorController:
    if device == "test":
        return FakeMotorController()
    if device == "pi":
        return FreenoveMotorController()
    raise ValueError(f"Invalid device: {device!r}")


def main() -> int:
    args = parse_args()

    motor_ctl = build_motor_controller(args.hardware)
    motor_cfg = load_motor_config(args.car_cfg)

    driver = MotorDriver(motor_ctl, motor_cfg)

    try:
        driver.drive(2500, 0)
        sleep(2)
    except KeyboardInterrupt:
        return -1
    

    finally:
        driver.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())