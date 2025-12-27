from __future__ import annotations

import threading
from time import sleep

from carbot.config.models import CameraPolicy
from carbot.contracts.camera_controller import BGRFrame, CameraController


class CameraDriver:
    def __init__(self, controller: CameraController, policy: CameraPolicy) -> None:
        self._ctl = controller
        self._policy = policy

        self._lock = threading.Lock()
        self._latest: BGRFrame | None = None

        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("CameraDriver already started")

        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop,
            name="camera-capture",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

        thread = self._thread
        self._thread = None
        if thread is not None:
            thread.join(timeout=float(self._policy.time_limit))

        self._ctl.close()

    def close(self) -> None:
        self.stop()

    def latest_frame(self) -> BGRFrame | None:
        """
        Returns the most recent frame.

        The returned object will not be changed by the next update (the driver swaps
        _latest to a new BGRFrame each time). Treat frame.img as read-only; if you
        need to mutate it, make your own copy in the caller.
        """
        with self._lock:
            return self._latest

    def _loop(self) -> None:
        while not self._stop.is_set():
            got_frame = False

            for _ in range(self._policy.retries + 1):
                if self._stop.is_set():
                    return

                frame = self._ctl.try_read_frame()
                if frame is not None:
                    with self._lock:
                        self._latest = frame
                    got_frame = True
                    break

            if not got_frame:
                sleep(float(self._policy.idle_sleep))
