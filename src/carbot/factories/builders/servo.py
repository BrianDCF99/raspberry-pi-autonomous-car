from __future__ import annotations

from carbot.config.loader import load_servo_config
from carbot.drivers.servo_driver import ServoDriver
from carbot.factories._utils import resolve_factory
from carbot.factories.registries import SERVO_CONTROLLERS


def build_servo_driver(*, controller: str, cfg: str) -> ServoDriver:
    servo_cfg = load_servo_config(cfg)
    controller_factory = resolve_factory(
        SERVO_CONTROLLERS, controller, registry_name="servo_controller"
    )
    servo_ctl = controller_factory()
    return ServoDriver(servo_ctl, servo_cfg)
