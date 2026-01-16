from __future__ import annotations

from carbot.config.loader import load_camera_config, load_camera_policy
from carbot.drivers.camera_driver import CameraDriver
from carbot.factories._utils import resolve_factory
from carbot.factories.registries import CAMERA_CONTROLLERS


def build_camera_driver(*, controller: str, cfg: str, policy: str) -> CameraDriver:
    camera_cfg = load_camera_config(cfg)
    camera_policy = load_camera_policy(policy)

    controller_factory = resolve_factory(
        CAMERA_CONTROLLERS, controller, registry_name="camera_controller"
    )
    camera_ctl = controller_factory(camera_cfg)

    return CameraDriver(camera_ctl, camera_cfg, camera_policy)
