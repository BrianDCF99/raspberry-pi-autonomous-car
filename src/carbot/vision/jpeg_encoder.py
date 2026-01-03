# carbot/services/jpeg_encoder_service.py
from __future__ import annotations

import threading

import cv2 as cv
import numpy as np

from carbot.vision.latest_store import LatestStore


class _JpegEncoderWorker(threading.Thread):
    def __init__(
        self,
        *,
        in_store: LatestStore[np.ndarray],
        out_store: LatestStore[bytes],
        stop_event: threading.Event,
        jpeg_quality: int,
    ) -> None:
        super().__init__(name="jpeg-encoder-worker", daemon=True)
        self._in = in_store
        self._out = out_store
        self._stop = stop_event
        self._quality = max(10, min(int(jpeg_quality), 95))

    def run(self) -> None:
        encode_params = [int(cv.IMWRITE_JPEG_QUALITY), self._quality]
        last_ts = 0

        while not self._stop.is_set():
            img, ts = self._in.wait_newer(
                last_timestamp_ns=last_ts,
                stop_event=self._stop,
                timeout_s=0.5,
            )
            if img is None:
                continue

            last_ts = ts

            # OpenCV encoding is happiest with contiguous memory
            img = np.ascontiguousarray(img)

            ok, buffer = cv.imencode(".jpg", img, encode_params)
            if not ok:
                continue

            self._out.set(buffer.tobytes(), timestamp_ns=ts)


class JpegEncoderService:
    """
    Encodes processed frames to JPEG and publishes JPEG bytes.
    """

    def __init__(
        self,
        *,
        in_store: LatestStore[np.ndarray],
        jpeg_quality: int,
    ) -> None:
        self._stop = threading.Event()
        self._store: LatestStore[bytes] = LatestStore()
        self._worker = _JpegEncoderWorker(
            in_store=in_store,
            out_store=self._store,
            stop_event=self._stop,
            jpeg_quality=jpeg_quality,
        )

    @property
    def store(self) -> LatestStore[bytes]:
        return self._store

    def start(self) -> None:
        if self._worker.is_alive():
            return
        self._stop.clear()
        self._worker.start()

    def close(self) -> None:
        if self._stop.is_set():
            return
        self._stop.set()
        if self._worker.is_alive():
            self._worker.join(timeout=2.0)