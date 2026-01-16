from __future__ import annotations

import threading
from time import monotonic, sleep
from typing import NamedTuple

from carbot.config.models import InfraredConfig
from carbot.contracts.infrared_controller import Channel, InfraredController


class InfraredSample(NamedTuple):
    left: int
    middle: int
    right: int
    bits: int
    seq: int


class InfraredDriver:
    def __init__(self, controller: InfraredController, cfg: InfraredConfig) -> None:
        self._ctl = controller
        self._cfg = cfg

        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)

        self._latest: InfraredSample | None = None
        self._seq: int = 0

        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._closed = False

    @property
    def cfg(self) -> InfraredConfig:
        return self._cfg

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("InfraredDriver already started")
        if self._closed:
            raise RuntimeError("InfraredDriver is closed")

        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop,
            name="infrared-poll",
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

    def latest(self) -> InfraredSample | None:
        with self._lock:
            return self._latest

    def wait_next(
        self,
        last_seq: int | None = None,
        *,
        timeout: float | None = None,
    ) -> InfraredSample | None:
        """
        Blocks until a newer sample than `last_seq` arrives, or timeout/stop happens.
        Returns the newest sample (or None if none exists yet and we stop/timeout).
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

            return self._latest

    def _loop(self) -> None:
        hz = float(self._cfg.hz)
        interval = (1.0 / hz) if hz > 0 else 0.5

        next_t = monotonic()
        while not self._stop.is_set():
            r = self._ctl.read_channel(Channel.RIGHT)
            m = self._ctl.read_channel(Channel.MIDDLE)
            l = self._ctl.read_channel(Channel.LEFT)
            bits = (l << 2) | (m << 1) | r

            with self._cond:
                self._seq += 1
                self._latest = InfraredSample(
                    left=l, middle=m, right=r, bits=bits, seq=self._seq
                )
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
