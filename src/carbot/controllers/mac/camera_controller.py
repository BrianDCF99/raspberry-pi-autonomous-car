from time import monotonic_ns

import cv2 as cv

from carbot.config.models import CameraConfig
from carbot.contracts.camera_controller import BGRFrame, CameraController


class MacCameraController(CameraController):
    def __init__(self, cfg: CameraConfig) -> None:
        if cfg.fps <= 0:
            raise ValueError("fps must be > 0")

        cap = cv.VideoCapture(cfg.device_idx, cv.CAP_AVFOUNDATION)

        if not cap.isOpened():
            cap.release()
            raise RuntimeError(
                f"Failed to open Mac's camera on index: {cfg.device_idx}"
            )

        cap.set(cv.CAP_PROP_FRAME_WIDTH, cfg.width)
        cap.set(cv.CAP_PROP_FRAME_HEIGHT, cfg.height)
        cap.set(cv.CAP_PROP_FPS, cfg.fps)

        self._cap = cap

    def close(self) -> None:
        self._cap.release()

    def try_read_frame(self) -> BGRFrame | None:
        ok, img = self._cap.read()
        if not ok or img is None:
            return None
        return BGRFrame(img=img, timestamp=monotonic_ns())
