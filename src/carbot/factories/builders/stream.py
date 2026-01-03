from __future__ import annotations

from carbot.config.loader import load_network_config
from carbot.drivers.camera_driver import CameraDriver
from carbot.vision.frame_pipeline import FramePipelineService
from carbot.vision.jpeg_encoder import JpegEncoderService
from carbot.vision.pipelines import crop_bottom_quarter
from carbot.vision.stream_service import StreamingService


def build_streaming_service(
    *, camera_driver: CameraDriver, networking_cfg: str
) -> StreamingService:
    net_cfg = load_network_config(networking_cfg)

    pipeline = FramePipelineService(
        driver=camera_driver,
        transform=crop_bottom_quarter,  # swap this to try different pipelines
        idle_sleep_s=net_cfg.idle_sleep_s,
    )
    encoder = JpegEncoderService(
        in_store=pipeline.store,
        jpeg_quality=net_cfg.jpeg_quality,
    )

    pipeline.start()
    encoder.start()

    return StreamingService(jpeg_store=encoder.store, cfg=net_cfg)