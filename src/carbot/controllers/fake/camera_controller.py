from __future__ import annotations

from time import monotonic_ns

import numpy as np

from carbot.contracts.camera_controller import BGRFrame, CameraController


class FakeCameraController(CameraController):
    def __init__(self) -> None:
        self._newest: BGRFrame | None = None
        print("Initializing Fake Camera Controller")

    def close(self) -> None:
        print("Closing Fake Camera Controller")

    def set_frame(self, image: np.ndarray) -> None:
        self._newest = BGRFrame(image.copy(), monotonic_ns())

    def try_read_frame(self) -> BGRFrame | None:
        return self._newest
