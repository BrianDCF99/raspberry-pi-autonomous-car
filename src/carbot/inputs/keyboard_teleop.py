from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from select import select
from time import monotonic
from typing import Optional

import fcntl
import sys
import termios
import tty

from carbot.control.commands import MotorCommand, ServoCommand


@dataclass(frozen=True, slots=True)
class KeyboardTeleopConfig:
    speed: int = 1500
    steer: int = 1500

    servo_step: int = 20

    poll_s: float = 0.02
    deadman_s: float = 0.15  # no key repeats recently -> motor stop

    invert_steer: bool = False
    invert_pan: bool = False
    invert_tilt: bool = False

    debug_keys: bool = False


class KeyboardTeleop:
    """
    Motor:
      - arrows: up/down = forward/back, left/right = in-place steer
      - u/o/j/l: diagonal arcs
      - space: stop
    Servo:
      - wasd: relative angle nudges (pan/tilt)
      - c: center (pan=0, tilt=0)
    Quit:
      - q or Ctrl+C
    """
    def __init__(self, cfg: KeyboardTeleopConfig) -> None:
        self._cfg = cfg

        self._lock = threading.Lock()

        self._latest_motor: MotorCommand | None = None
        self._latest_servo: ServoCommand | None = None

        self._pan = 0
        self._tilt = 0

        self._last_motor_input_t = monotonic()

        self._quit = threading.Event()
        self._stop = threading.Event()

        self._thread: threading.Thread | None = None
        self._thread_exc: BaseException | None = None

        self._last_key: str | None = None
        self._last_bytes: bytes = b""
        self._last_read_t: float = 0.0

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("KeyboardTeleop already started")

        self._stop.clear()
        self._thread_exc = None

        self._thread = threading.Thread(
            target=self._thread_main,
            name="keyboard-teleop",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        t = self._thread
        self._thread = None
        if t is not None:
            t.join(timeout=1.0)

    def close(self) -> None:
        self.stop()

    @property
    def quit_requested(self) -> bool:
        return self._quit.is_set()

    @property
    def alive(self) -> bool:
        t = self._thread
        return bool(t and t.is_alive())

    def thread_error(self) -> BaseException | None:
        with self._lock:
            return self._thread_exc

    def debug_last_key(self) -> tuple[str | None, bytes, float]:
        with self._lock:
            return self._last_key, self._last_bytes, self._last_read_t

    # --- Sources ---
    def latest_motor(self) -> Optional[MotorCommand]:
        with self._lock:
            if self._latest_motor is None:
                return None
            if (monotonic() - self._last_motor_input_t) >= float(self._cfg.deadman_s):
                return MotorCommand.stop()
            return self._latest_motor

    def latest_servo(self) -> Optional[ServoCommand]:
        with self._lock:
            return self._latest_servo

    # mux expects Source.latest() -> Optional[T]
    def latest(self) -> Optional[MotorCommand]:
        return self.latest_motor()

    # --- Thread wrapper (captures exceptions) ---
    def _thread_main(self) -> None:
        try:
            self._loop()
        except BaseException as e:
            with self._lock:
                self._thread_exc = e
            # force quit so runners can exit cleanly
            self._quit.set()

    # --- Internals ---
    def _loop(self) -> None:
        fd = sys.stdin.fileno()

        # If this fails in your environment, you'll see it via thread_error()
        old_term = termios.tcgetattr(fd)
        old_flags = fcntl.fcntl(fd, fcntl.F_GETFL)

        try:
            tty.setraw(fd)
            fcntl.fcntl(fd, fcntl.F_SETFL, old_flags | os.O_NONBLOCK)

            # flush queued input
            for _ in range(10):
                _ = self._read_available(fd, timeout=0.0)

            buf = ""
            while not self._stop.is_set() and not self._quit.is_set():
                data = self._read_available(fd, timeout=float(self._cfg.poll_s))
                if data:
                    with self._lock:
                        self._last_bytes = data
                        self._last_read_t = monotonic()
                    buf += data.decode("latin-1")

                while True:
                    k, buf = self._pop_key(buf)
                    if k is None:
                        break
                    with self._lock:
                        self._last_key = k
                    self._handle_key(k)

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_term)
            fcntl.fcntl(fd, fcntl.F_SETFL, old_flags)

    @staticmethod
    def _read_available(fd: int, *, timeout: float) -> bytes:
        r, _, _ = select([fd], [], [], timeout)
        if not r:
            return b""
        try:
            return os.read(fd, 64)
        except BlockingIOError:
            return b""

    @staticmethod
    def _pop_key(buf: str) -> tuple[str | None, str]:
        if not buf:
            return None, buf

        # arrows are ESC [ A/B/C/D
        if buf[0] == "\x1b":
            if len(buf) < 3:
                return None, buf
            if buf[1] == "[" and buf[2] in ("A", "B", "C", "D"):
                return buf[:3], buf[3:]
            return "\x1b", buf[1:]

        return buf[0], buf[1:]

    def _set_motor(self, throttle: int, steer_differential: int) -> None:
        steer = -steer_differential if self._cfg.invert_steer else steer_differential
        with self._lock:
            self._latest_motor = MotorCommand.now(throttle, steer)
            self._last_motor_input_t = monotonic()

    def _set_servo(self, pan: int, tilt: int) -> None:
        with self._lock:
            self._latest_servo = ServoCommand.now(pan, tilt)

    def _handle_key(self, k: str) -> None:
        # Ctrl+C in raw mode becomes a literal byte 0x03, not KeyboardInterrupt
        if k == "\x03":
            self._quit.set()
            return

        if k == "q":
            self._quit.set()
            return

        # motor stop
        if k == " ":
            self._set_motor(0, 0)
            return

        speed = int(self._cfg.speed)
        steer = int(self._cfg.steer)

        # motor arrows
        if k == "\x1b[A":  # up
            self._set_motor(speed, 0)
            return
        if k == "\x1b[B":  # down
            self._set_motor(-speed, 0)
            return
        if k == "\x1b[C":  # right (in-place)
            self._set_motor(0, steer)
            return
        if k == "\x1b[D":  # left (in-place)
            self._set_motor(0, -steer)
            return

        # motor diagonals (arcs)
        if k == "o":  # forward-right arc
            self._set_motor(speed, steer)
            return
        if k == "u":  # forward-left arc
            self._set_motor(speed, -steer)
            return
        if k == "l":  # backward-right arc
            self._set_motor(-speed, -steer)
            return
        if k == "j":  # backward-left arc
            self._set_motor(-speed, steer)
            return

        # servo (relative angles)
        step = int(self._cfg.servo_step)
        pan_sign = -1 if self._cfg.invert_pan else 1
        tilt_sign = -1 if self._cfg.invert_tilt else 1

        kk = k.lower()
        if kk == "c":
            self._pan = 0
            self._tilt = 0
            self._set_servo(self._pan, self._tilt)
            return

        if kk == "a":
            self._pan -= step * pan_sign
            self._set_servo(self._pan, self._tilt)
            return
        if kk == "d":
            self._pan += step * pan_sign
            self._set_servo(self._pan, self._tilt)
            return
        if kk == "w":
            self._tilt += step * tilt_sign
            self._set_servo(self._pan, self._tilt)
            return
        if kk == "s":
            self._tilt -= step * tilt_sign
            self._set_servo(self._pan, self._tilt)
            return