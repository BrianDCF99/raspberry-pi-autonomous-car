from __future__ import annotations

from carbot.config.loader import load_infrared_config
from carbot.drivers.infrared_driver import InfraredDriver
from carbot.factories._utils import resolve_factory
from carbot.factories.registries import INFRARED_CONTROLLERS


def build_infrared_driver(*, controller: str, cfg: str) -> InfraredDriver:
    infrared_cfg = load_infrared_config(cfg)
    controller_factory = resolve_factory(
        INFRARED_CONTROLLERS, controller, registry_name="infrared_controller"
    )
    infrared_ctl = controller_factory()
    return InfraredDriver(infrared_ctl, infrared_cfg)
