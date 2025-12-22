from __future__ import annotations
from collections.abc import Callable
import argparse
from time import sleep
from carbot.contracts.ultrasonic_controller import UltrasonicController
from carbot.controllers.freenove.ultrasonic_controller import FreenoveUltrasonicController
from carbot.controllers.fake.ultrasonic_controller import FakeUltrasonicController
from carbot.drivers.ultrasonic_driver import UltrasonicDriver

CONTROLLERS: dict[str, Callable[[], UltrasonicController]] = {
    "test": FakeUltrasonicController,
    "freenove": FreenoveUltrasonicController,
}

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--controller", choices=sorted(CONTROLLERS), default="test")
    p.add_argument("--hz", type=float, default=2)
    return p.parse_args()

def main() -> int:
    print("Starting")
    args = parse_args()

    ultra_clt = CONTROLLERS[args.controller]()
    ultra_driver = UltrasonicDriver(ultra_clt)

    try:
        while True:
            distance = ultra_driver.read()
            message = (
                f"Distance: {distance} cm"
                if distance is not None
                else "No Distance Measured"
            )
            print(message)
            sleep(0.5)

    except KeyboardInterrupt:
        return 130

    finally:
        ultra_driver.close()



if __name__ == "__main__":
    raise SystemExit(main())
