from __future__ import annotations

from carbot.config.loader import load_network_config
from carbot.drivers.camera_driver import CameraDriver
from carbot.vision.stream_service import StreamingService


def build_streaming_service(
    *, camera_driver: CameraDriver, networking_cfg: str
) -> StreamingService:
    net_cfg = load_network_config(networking_cfg)
    return StreamingService(camera_driver, net_cfg)
