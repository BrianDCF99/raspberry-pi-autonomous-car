# carbot/services/streaming_service.py
from __future__ import annotations

import signal
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

import cv2 as cv

from carbot.config.models import NetworkConfig
from carbot.drivers.camera_driver import CameraDriver

_BOUNDARY = b"--frame"


class _JpegStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self._jpeg: bytes | None = None
        self._timestamp_ns: int = 0

    def set(self, jpeg: bytes, *, timestamp_ns: int) -> None:
        with self._cond:
            self._jpeg = jpeg
            self._timestamp_ns = timestamp_ns
            self._cond.notify_all()

    def get(self) -> tuple[bytes | None, int]:
        with self._lock:
            return self._jpeg, self._timestamp_ns

    def wait_newer(
        self, *, last_timestamp_ns: int, stop_event: threading.Event, timeout_s: float
    ) -> tuple[bytes | None, int]:
        deadline = time.monotonic() + timeout_s
        with self._cond:
            while not stop_event.is_set():
                jpeg = self._jpeg
                ts = self._timestamp_ns
                if jpeg is not None and ts != last_timestamp_ns:
                    return jpeg, ts

                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return None, last_timestamp_ns

                self._cond.wait(timeout=remaining)

            return None, last_timestamp_ns


class _JpegWorker(threading.Thread):
    def __init__(
        self,
        *,
        driver: CameraDriver,
        store: _JpegStore,
        stop_event: threading.Event,
        jpeg_quality: int,
        idle_sleep_s: float,
    ) -> None:
        super().__init__(name="mjpeg-jpeg-worker", daemon=True)
        self._driver = driver
        self._store = store
        self._stop_event = stop_event
        self._jpeg_quality = max(10, min(int(jpeg_quality), 95))
        self._idle_sleep_s = float(idle_sleep_s)

        self._last_frame_ts: int = 0

    def run(self) -> None:
        encode_params = [int(cv.IMWRITE_JPEG_QUALITY), self._jpeg_quality]

        while not self._stop_event.is_set():
            frame = self._driver.latest_frame()
            if frame is None:
                time.sleep(self._idle_sleep_s)
                continue

            if frame.timestamp == self._last_frame_ts:
                time.sleep(self._idle_sleep_s)
                continue

            self._last_frame_ts = frame.timestamp

            ok, buffer = cv.imencode(".jpg", frame.img, encode_params)
            if not ok:
                continue

            self._store.set(buffer.tobytes(), timestamp_ns=frame.timestamp)


class _ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True  # request threads won't block shutdown


class _Handler(BaseHTTPRequestHandler):
    store: _JpegStore
    stop_event: threading.Event

    def do_GET(self) -> None:  # noqa: N802
        if self.path in ("/", "/index.html"):
            self._serve_index()
            return
        if self.path.startswith("/snapshot.jpg"):
            self._serve_snapshot()
            return
        if self.path.startswith("/stream.mjpg"):
            self._serve_mjpeg()
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"not found")

    def _serve_index(self) -> None:
        html = b"""\
<html>
  <head><title>Carbot Stream</title></head>
  <body style="margin:0;background:#111;display:flex;justify-content:center;align-items:center;height:100vh;">
    <img src="/stream.mjpg" style="max-width:100%;max-height:100%;" />
  </body>
</html>
"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)

    def _serve_snapshot(self) -> None:
        jpeg, _ts = self.store.get()
        if jpeg is None:
            self.send_response(503)
            self.end_headers()
            self.wfile.write(b"no frame yet")
            return

        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(jpeg)))
        self.end_headers()
        self.wfile.write(jpeg)

    def _serve_mjpeg(self) -> None:
        self.send_response(200)
        self.send_header("Age", "0")
        self.send_header("Cache-Control", "no-cache, private")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.end_headers()

        last_ts = 0
        try:
            while not self.stop_event.is_set():
                jpeg, ts = self.store.wait_newer(
                    last_timestamp_ns=last_ts,
                    stop_event=self.stop_event,
                    timeout_s=1.0,
                )
                if jpeg is None:
                    continue

                last_ts = ts
                self.wfile.write(_BOUNDARY + b"\r\n")
                self.wfile.write(b"Content-Type: image/jpeg\r\n")
                self.wfile.write(f"Content-Length: {len(jpeg)}\r\n\r\n".encode())
                self.wfile.write(jpeg)
                self.wfile.write(b"\r\n")
        except (BrokenPipeError, ConnectionResetError):
            return

    def log_message(self, fmt: str, *args) -> None:
        return  # silence request spam


class StreamingService:
    def __init__(self, driver: CameraDriver, cfg: NetworkConfig) -> None:
        self._driver = driver
        self._cfg = cfg

        self._stop_event = threading.Event()
        self._store = _JpegStore()
        self._jpeg_worker = _JpegWorker(
            driver=self._driver,
            store=self._store,
            stop_event=self._stop_event,
            jpeg_quality=cfg.jpeg_quality,
            idle_sleep_s=cfg.idle_sleep_s,
        )

        handler_cls = type("InjectedHandler", (_Handler,), {})
        handler_cls.store = self._store
        handler_cls.stop_event = self._stop_event

        self._httpd = _ThreadedHTTPServer((cfg.host, cfg.port), handler_cls)

    def serve_forever(self) -> None:
        self._jpeg_worker.start()
        try:
            self._httpd.serve_forever(poll_interval=0.2)
        finally:
            self.close()

    def close(self) -> None:
        if self._stop_event.is_set():
            return

        self._stop_event.set()

        self._httpd.shutdown()
        self._httpd.server_close()

        if self._jpeg_worker.is_alive():
            self._jpeg_worker.join(timeout=2.0)


def install_signal_handlers(stop_fn) -> None:
    def _sig(_signum, _frame) -> None:
        stop_fn()

    signal.signal(signal.SIGINT, _sig)
    signal.signal(signal.SIGTERM, _sig)
