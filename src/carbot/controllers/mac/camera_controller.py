from time import monotonic_ns

import cv2 as cv

from carbot.contracts.camera_controller import BGRFrame, CameraController


class MacCameraController(CameraController):
    def __init__(
        self,
        device_idx: int = 0,
        width: int = 640,
        height: int = 480,
        fps: int = 30,
    ) -> None:
        cap = cv.VideoCapture(device_idx, cv.CAP_AVFOUNDATION)

        if not self._cap.isOpened():
            raise RuntimeError(f"Failed to open Mac's camera on index: {device_idx}")

        cap.set(cv.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv.CAP_PROP_FPS, fps)

        self._cap = cap

    def close(self) -> None:
        self._cap.release()

    def try_read_frame(self) -> BGRFrame | None:
        ok, img = self._cap.read()
        if not ok or img is None:
            return None
        return BGRFrame(img=img, timestamp_ns=monotonic_ns())
