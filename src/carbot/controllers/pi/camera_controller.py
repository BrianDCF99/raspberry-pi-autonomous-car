from __future__ import annotations

from time import monotonic_ns

import cv2 as cv
from picamera2 import Picamera2

from carbot.config.models import CameraConfig
from carbot.contracts.camera_controller import BGRFrame, CameraController


class PiCameraController(CameraController):
    def __init__(self, cfg: CameraConfig) -> None:
        if cfg.fps <= 0:
            raise ValueError("fps must be > 0")

        self._cam = Picamera2()
        self._started = False

        # Prefer simple FrameRate control; fall back to FrameDurationLimits if needed.
        try:
            cfg = self._cam.create_video_configuration(
                main={"size": (cfg.width, cfg.height), "format": "RGB888"},
                controls={"FrameRate": cfg.fps},
            )
        except TypeError:
            frame_us = int(1_000_000 / cfg.fps)
            cfg = self._cam.create_video_configuration(
                main={"size": (cfg.width, cfg.height), "format": "RGB888"},
                controls={"FrameDurationLimits": (frame_us, frame_us)},
            )

        self._cam.configure(cfg)
        self._cam.start()
        self._started = True

    def close(self) -> None:
        try:
            if self._started:
                self._cam.stop()
                self._started = False
        finally:
            self._cam.close()

    def try_read_frame(self) -> BGRFrame | None:
        if not self._started:
            raise RuntimeError("Camera not started")

        rgb = self._cam.capture_array()
        if rgb is None:
            return None

        bgr = cv.cvtColor(rgb, cv.COLOR_RGB2BGR)
        return BGRFrame(img=bgr, timestamp_ns=monotonic_ns())
