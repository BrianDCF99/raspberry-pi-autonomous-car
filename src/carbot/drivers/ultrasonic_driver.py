from __future__ import annotations

import threading
from time import monotonic, sleep

from carbot.config.models import UltrasonicConfig
from carbot.contracts.ultrasonic_controller import UltrasonicController


class UltrasonicDriver:
    def __init__(self, controller: UltrasonicController, cfg: UltrasonicConfig) -> None:
        self._ctl = controller
        self._cfg = cfg

        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)

        self._latest: float | None = None
        self._seq: int = 0

        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._closed = False

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("UltrasonicDriver already started")
        if self._closed:
            raise RuntimeError("UltrasonicDriver is closed")

        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop,
            name="ultrasonic-poll",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

        thread = self._thread
        self._thread = None
        if thread is not None:
            thread.join(timeout=float(self._cfg.time_limit))

        self._close_controller()

    def close(self) -> None:
        self.stop()

    def latest(self) -> float | None:
        with self._lock:
            return self._latest

    def wait_next(
        self, last_seq: int | None = None, *, timeout: float | None = None
    ) -> tuple[int, float] | None:
        """
        Wait until a newer measurement than last_seq is available.
        Returns (seq, distance) or None on timeout/stop/no data yet.
        """
        with self._cond:
            if last_seq is None:
                last_seq = self._seq

            deadline = None if timeout is None else (monotonic() + float(timeout))

            while not self._stop.is_set() and self._seq == last_seq:
                if deadline is None:
                    self._cond.wait()
                else:
                    remaining = deadline - monotonic()
                    if remaining <= 0:
                        break
                    self._cond.wait(timeout=remaining)

            if self._latest is None:
                return None
            return (self._seq, self._latest)

    def _loop(self) -> None:
        hz = float(self._cfg.hz)
        interval = (1.0 / hz) if hz > 0 else 0.5

        next_t = monotonic()
        while not self._stop.is_set():
            try:
                dist = self._ctl.read_distance()
            except Exception:
                # don't kill the thread; back off a bit
                sleep(0.05)
                next_t = monotonic()
                continue

            with self._cond:
                self._seq += 1
                self._latest = dist
                self._cond.notify_all()

            next_t += interval
            delay = next_t - monotonic()
            if delay > 0:
                sleep(delay)
            else:
                next_t = monotonic()

    def _close_controller(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True

        self._ctl.close()
