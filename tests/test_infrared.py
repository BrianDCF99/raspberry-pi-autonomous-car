import argparse
from collections.abc import Callable
from time import sleep

from carbot.contracts.infrared_controller import InfraredController
from carbot.controllers.fake.infrared_controller import FakeInfraredController
from carbot.controllers.freenove.infrared_controller import FreenoveInfraredController
from carbot.drivers.infrared_driver import InfraredDriver

CONTROLLERS: dict[str, Callable[[], InfraredController]] = {
    "test": FakeInfraredController,
    "freenove": FreenoveInfraredController,
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--controller", choices=sorted(CONTROLLERS), default="test")
    p.add_argument("--hz", type=float, default=2)
    return p.parse_args()


def main() -> int:
    args = parse_args()

    infrared_ctl = CONTROLLERS[args.controller]()
    driver = InfraredDriver(infrared_ctl)

    period = 1.0 / args.hz if args.hz > 0 else 0.5

    try:
        while True:
            bits = driver.read_bits()
            l, m, r = driver.read_tuple()
            print(f"Bits:  {bits:03b} \t Tuple: {l, m ,r}")
            sleep(period)

    except KeyboardInterrupt:
        return 130

    finally:
        driver.close()


if __name__ == "__main__":
    raise SystemExit(main())
