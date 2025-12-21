import argparse
from collections.abc import Callable
from time import sleep

from carbot.controllers.freenove.servo_controller import FreenoveServoController
from carbot.config.loader import load_servo_config
from carbot.contracts.servo_controller import ServoController
from carbot.controllers.fake.servo_controller import FakeServoController
from carbot.drivers.servo_driver import ServoDriver

CONTROLLERS: dict[str, Callable[[], ServoController]] = {
    "test": FakeServoController,
    "freenove": FreenoveServoController,
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--controller", choices=sorted(CONTROLLERS), default="test")
    p.add_argument("--servo-cfg", default="freenove")
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

    servo_ctl = CONTROLLERS[args.controller]()
    servo_cfg = load_servo_config(args.servo_cfg)

    driver = ServoDriver(servo_ctl, servo_cfg)

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
