# carbot/inputs/terminal_kb_teleop.py
from __future__ import annotations

import os
import sys
import threading
from select import select
from time import monotonic
from typing import Final

import fcntl
import termios
import tty

from carbot.config.models import TeleopConfig, TeleopKeymap
from carbot.control.commands import MotorCommand, ServoCommand
from carbot.inputs.teleop import Teleop


class TerminalKeyboardTeleop(Teleop):
    """
    Reads sys.stdin in raw TTY mode (escape sequences for arrows) and emits commands.
    """

    _READ_SIZE: Final[int] = 64
    _FLUSH_PASSES: Final[int] = 10

    def __init__(self, cfg: TeleopConfig) -> None:
        self._cfg = cfg
        self._keys = cfg.keymap

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

    @property
    def cfg(self) -> TeleopConfig:
        return self._cfg

    @property
    def keymap(self) -> TeleopKeymap:
        return self._keys

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

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("TerminalKeyboardTeleop already started")
        if not sys.stdin.isatty():
            raise RuntimeError("stdin is not a TTY. Terminal keyboard teleop needs an interactive terminal.")

        self._stop.clear()
        self._quit.clear()
        with self._lock:
            self._thread_exc = None

        self._thread = threading.Thread(
            target=self._thread_main,
            name="terminal-keyboard-teleop",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        t = self._thread
        self._thread = None
        if t is not None:
            t.join(timeout=1.0)

    def latest_motor(self) -> MotorCommand | None:
        with self._lock:
            if self._latest_motor is None:
                return None

            if (monotonic() - self._last_motor_input_t) >= float(self._cfg.deadman_s):
                return MotorCommand.stop()

            return self._latest_motor

    def latest_servo(self) -> ServoCommand | None:
        with self._lock:
            return self._latest_servo

    def _thread_main(self) -> None:
        try:
            self._loop()
        except BaseException as e:
            with self._lock:
                self._thread_exc = e
            self._quit.set()

    def _loop(self) -> None:
        fd = sys.stdin.fileno()
        old_term = termios.tcgetattr(fd)
        old_flags = fcntl.fcntl(fd, fcntl.F_GETFL)

        try:
            tty.setraw(fd)
            fcntl.fcntl(fd, fcntl.F_SETFL, old_flags | os.O_NONBLOCK)

            for _ in range(self._FLUSH_PASSES):
                _ = self._read_available(fd, timeout=0.0)

            buf = ""
            while not self._stop.is_set() and not self._quit.is_set():
                data = self._read_available(fd, timeout=float(self._cfg.poll_s))
                if data:
                    now = monotonic()
                    with self._lock:
                        self._last_bytes = data
                        self._last_read_t = now
                    buf += data.decode("latin-1", errors="ignore")

                while True:
                    k, buf = self._pop_key(buf)
                    if k is None:
                        break

                    k_norm = k.lower() if len(k) == 1 else k
                    with self._lock:
                        self._last_key = k_norm
                    self._handle_key(k_norm)

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_term)
            fcntl.fcntl(fd, fcntl.F_SETFL, old_flags)

    @classmethod
    def _read_available(cls, fd: int, *, timeout: float) -> bytes:
        r, _, _ = select([fd], [], [], timeout)
        if not r:
            return b""
        try:
            return os.read(fd, cls._READ_SIZE)
        except BlockingIOError:
            return b""

    @staticmethod
    def _pop_key(buf: str) -> tuple[str | None, str]:
        if not buf:
            return None, buf

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
        if k in self._keys.quit:
            self._quit.set()
            return

        speed = int(self._cfg.speed)
        steer = int(self._cfg.steer)

        if k in self._keys.motor_stop:
            self._set_motor(0, 0)
            return

        if k in self._keys.motor_forward:
            self._set_motor(speed, 0)
            return
        if k in self._keys.motor_backward:
            self._set_motor(-speed, 0)
            return
        if k in self._keys.motor_right:
            self._set_motor(0, steer)
            return
        if k in self._keys.motor_left:
            self._set_motor(0, -steer)
            return

        if k in self._keys.motor_fwd_right:
            self._set_motor(speed, steer)
            return
        if k in self._keys.motor_fwd_left:
            self._set_motor(speed, -steer)
            return
        if k in self._keys.motor_back_right:
            self._set_motor(-speed, -steer)
            return
        if k in self._keys.motor_back_left:
            self._set_motor(-speed, steer)
            return

        step = int(self._cfg.servo_step)
        pan_sign = -1 if self._cfg.invert_pan else 1
        tilt_sign = -1 if self._cfg.invert_tilt else 1

        if k in self._keys.servo_center:
            self._pan = 0
            self._tilt = 0
            self._set_servo(self._pan, self._tilt)
            return

        if k in self._keys.servo_pan_left:
            self._pan -= step * pan_sign
            self._set_servo(self._pan, self._tilt)
            return
        if k in self._keys.servo_pan_right:
            self._pan += step * pan_sign
            self._set_servo(self._pan, self._tilt)
            return
        if k in self._keys.servo_tilt_up:
            self._tilt += step * tilt_sign
            self._set_servo(self._pan, self._tilt)
            return
        if k in self._keys.servo_tilt_down:
            self._tilt -= step * tilt_sign
            self._set_servo(self._pan, self._tilt)
            return


# Back-compat for existing imports
KeyboardTeleop = TerminalKeyboardTeleop