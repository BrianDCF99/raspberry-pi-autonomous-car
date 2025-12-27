from __future__ import annotations

from carbot.config.loader import load_motor_config
from carbot.drivers.motor_driver import MotorDriver
from carbot.factories._utils import resolve_factory
from carbot.factories.registries import MOTOR_CONTROLLERS


def build_motor_driver(*, controller: str, cfg: str) -> MotorDriver:
    motor_cfg = load_motor_config(cfg)
    controller_factory = resolve_factory(
        MOTOR_CONTROLLERS, controller, registry_name="motor_controller"
    )
    motor_ctl = controller_factory()
    return MotorDriver(motor_ctl, motor_cfg)
