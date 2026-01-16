# carbot/services/streaming_service.py
from __future__ import annotations

import signal
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

import numpy as np

from carbot.config.models import NetworkConfig
from carbot.vision.latest_store import LatestStore

_BOUNDARY = b"--frame"


class _ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class _Handler(BaseHTTPRequestHandler):
    store: LatestStore[bytes]
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
        return


class StreamingService:
    def __init__(
        self,
        *,
        jpeg_store: LatestStore[bytes],
        cfg: NetworkConfig,
        frame_store: LatestStore[np.ndarray] | None = None,
    ) -> None:
        self._cfg = cfg
        self._stop_event = threading.Event()

        # expose stores for consumers (logging / dataset capture / debugging)
        self._jpeg_store = jpeg_store
        self._frame_store = frame_store

        handler_cls = type("InjectedHandler", (_Handler,), {})
        handler_cls.store = jpeg_store
        handler_cls.stop_event = self._stop_event

        self._httpd = _ThreadedHTTPServer((cfg.host, cfg.port), handler_cls)

    def serve_forever(self) -> None:
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

    def latest_jpeg(self) -> tuple[bytes | None, int]:
        return self._jpeg_store.get()

    def latest_frame(self) -> tuple[np.ndarray | None, int]:
        if self._frame_store is None:
            return None, 0
        return self._frame_store.get()


def install_signal_handlers(stop_fn) -> None:
    def _sig(_signum, _frame) -> None:
        stop_fn()

    signal.signal(signal.SIGINT, _sig)
    signal.signal(signal.SIGTERM, _sig)