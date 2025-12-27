from __future__ import annotations

from carbot.config.loader import load_infrared_config
from carbot.drivers.ultrasonic_driver import UltrasonicDriver
from carbot.factories._utils import resolve_factory
from carbot.factories.registries import ULTRASONIC_CONTROLLERS


def build_ultrasonic_driver(*, controller: str, cfg: str) -> UltrasonicDriver:
    ultrasonic_cfg = load_infrared_config(cfg)
    controller_factory = resolve_factory(
        ULTRASONIC_CONTROLLERS, controller, registry_name="ultrasonic_controller"
    )
    ultrasonic_ctl = controller_factory()
    return UltrasonicDriver(ultrasonic_ctl, ultrasonic_cfg)
