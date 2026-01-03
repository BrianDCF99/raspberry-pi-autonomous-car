# carbot/services/frame_pipeline_service.py
from __future__ import annotations

import threading
import time

import numpy as np

from carbot.drivers.camera_driver import CameraDriver
from carbot.vision.latest_store import LatestStore
from carbot.vision.pipelines import FrameTransform


class _PipelineWorker(threading.Thread):
    def __init__(
        self,
        *,
        driver: CameraDriver,
        out_store: LatestStore[np.ndarray],
        stop_event: threading.Event,
        idle_sleep_s: float,
        transform: FrameTransform,
    ) -> None:
        super().__init__(name="frame-pipeline-worker", daemon=True)
        self._driver = driver
        self._out = out_store
        self._stop = stop_event
        self._idle_sleep_s = float(idle_sleep_s)
        self._transform = transform
        self._last_ts: int = 0

    def run(self) -> None:
        while not self._stop.is_set():
            frame = self._driver.latest_frame()
            if frame is None:
                time.sleep(self._idle_sleep_s)
                continue

            ts = int(frame.timestamp)
            if ts == self._last_ts:
                time.sleep(self._idle_sleep_s)
                continue

            img = frame.img  # treat as read-only
            try:
                processed = self._transform(img)
            except Exception:
                # keep running even if pipeline breaks for a frame
                time.sleep(self._idle_sleep_s)
                continue

            self._last_ts = ts
            self._out.set(processed, timestamp_ns=ts)


class FramePipelineService:
    """
    Reads raw frames from CameraDriver, applies a transform, publishes processed frames.
    """

    def __init__(
        self,
        *,
        driver: CameraDriver,
        transform: FrameTransform,
        idle_sleep_s: float = 0.005,
    ) -> None:
        self._stop = threading.Event()
        self._store: LatestStore[np.ndarray] = LatestStore()
        self._worker = _PipelineWorker(
            driver=driver,
            out_store=self._store,
            stop_event=self._stop,
            idle_sleep_s=idle_sleep_s,
            transform=transform,
        )

    @property
    def store(self) -> LatestStore[np.ndarray]:
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