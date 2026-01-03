# carbot/inputs/usb_kb_teleop.py
from __future__ import annotations

import threading
from select import select
from time import monotonic
from typing import Any, Final, Iterable

from carbot.config.models import TeleopConfig, TeleopKeymap
from carbot.control.commands import MotorCommand, ServoCommand
from carbot.inputs.teleop import Teleop


_EVDEV_SPECIAL_TO_TOKEN: dict[str, str] = {
    "KEY_UP": "\x1b[A",
    "KEY_DOWN": "\x1b[B",
    "KEY_RIGHT": "\x1b[C",
    "KEY_LEFT": "\x1b[D",
    "KEY_SPACE": " ",
    "KEY_ENTER": "\r",
    "KEY_TAB": "\t",
    "KEY_ESC": "\x1b",
}


def _keycode_to_token(keycode: str) -> str | None:
    special = _EVDEV_SPECIAL_TO_TOKEN.get(keycode)
    if special is not None:
        return special

    if not keycode.startswith("KEY_"):
        return None

    tail = keycode[4:]
    if len(tail) == 1 and tail.isalpha():
        return tail.lower()
    if len(tail) == 1 and tail.isdigit():
        return tail
    return None


def _as_set(xs: Iterable[str]) -> set[str]:
    return set(xs)


class UsbKeyboardTeleop(Teleop):
    """
    Uses /dev/input/event* via python-evdev.

    Key behavior:
    - Tracks currently pressed keys (DOWN/UP), so releasing RIGHT while holding FORWARD keeps moving forward.
    - Periodically refreshes motor timestamps while held (beats deadman).
    - Servo supports continuous movement while held + 2-axis combos (e.g. tilt-up + pan-left).
    """

    _SELECT_TIMEOUT_S: Final[float] = 0.01

    # Refresh motor command ts while keys are held so deadman doesn't stop you.
    _MOTOR_REFRESH_S: Final[float] = 0.03

    # How often to apply a servo "step" while a servo key is held.
    _SERVO_STEP_PERIOD_S: Final[float] = 0.04

    def __init__(
        self,
        cfg: TeleopConfig,
        *,
        device_path: str | None = None,
        grab: bool = False,
    ) -> None:
        self._cfg = cfg
        self._keys = cfg.keymap

        self._device_path = device_path
        self._grab = bool(grab)

        self._lock = threading.Lock()

        self._latest_motor: MotorCommand | None = None
        self._latest_servo: ServoCommand | None = None

        self._pan = 0
        self._tilt = 0
        self._last_motor_input_t = monotonic()

        self._pressed: set[str] = set()

        self._quit = threading.Event()
        self._stop = threading.Event()

        self._thread: threading.Thread | None = None
        self._thread_exc: BaseException | None = None

        # debug
        self._last_key: str | None = None
        self._last_bytes: bytes = b""
        self._last_read_t: float = 0.0

        # evdev glue (lazy import)
        self._dev: Any = None  # evdev.InputDevice
        self._ecodes: Any = None  # evdev.ecodes
        self._categorize: Any = None  # evdev.categorize
        self._KeyEvent: Any = None  # evdev.events.KeyEvent
        self._list_devices: Any = None  # evdev.list_devices
        self._InputDevice: Any = None  # evdev.InputDevice

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
            raise RuntimeError("UsbKeyboardTeleop already started")

        try:
            from evdev import InputDevice, categorize, ecodes, list_devices  # type: ignore
            from evdev.events import KeyEvent  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "UsbKeyboardTeleop requires python-evdev. Install with: pip install evdev"
            ) from e

        self._InputDevice = InputDevice
        self._categorize = categorize
        self._ecodes = ecodes
        self._list_devices = list_devices
        self._KeyEvent = KeyEvent

        self._open_device()

        self._stop.clear()
        self._quit.clear()
        with self._lock:
            self._thread_exc = None

        self._thread = threading.Thread(
            target=self._thread_main,
            name="usb-keyboard-teleop",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

        t = self._thread
        self._thread = None
        if t is not None:
            t.join(timeout=1.0)

        self._close_device()

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

    # -------- device handling --------

    def _open_device(self) -> None:
        path = self._device_path or self._auto_detect_keyboard()
        try:
            dev = self._InputDevice(path)
        except PermissionError as e:
            raise RuntimeError(
                f"Permission denied opening {path}. Add your user to the 'input' group or run with sudo."
            ) from e

        if self._grab:
            try:
                dev.grab()
            except Exception:
                pass

        self._dev = dev

    def _close_device(self) -> None:
        dev = self._dev
        self._dev = None
        if dev is None:
            return
        try:
            if self._grab:
                try:
                    dev.ungrab()
                except Exception:
                    pass
            dev.close()
        except Exception:
            pass

    def _auto_detect_keyboard(self) -> str:
        if self._list_devices is None:
            raise RuntimeError("evdev not available")

        candidates = list(self._list_devices())
        if not candidates:
            raise RuntimeError("No /dev/input/event* devices found")

        for path in candidates:
            dev = None
            try:
                dev = self._InputDevice(path)
                caps = dev.capabilities().get(self._ecodes.EV_KEY, [])
                if self._ecodes.KEY_A in caps and self._ecodes.KEY_SPACE in caps:
                    return path
            except Exception:
                continue
            finally:
                try:
                    if dev is not None:
                        dev.close()
                except Exception:
                    pass

        raise RuntimeError(
            "Could not auto-detect USB keyboard device. "
            "Pass device_path='/dev/input/eventX' to UsbKeyboardTeleop."
        )

    # -------- thread loop --------

    def _thread_main(self) -> None:
        try:
            self._loop()
        except BaseException as e:
            with self._lock:
                self._thread_exc = e
            self._quit.set()

    def _loop(self) -> None:
        dev = self._dev
        if dev is None:
            raise RuntimeError("USB keyboard device not open")

        fd = dev.fd

        motor_tokens = self._motor_tokens()
        servo_tokens = self._servo_tokens()

        last_motor_refresh_t = monotonic()
        last_servo_step_t = monotonic()

        while not self._stop.is_set() and not self._quit.is_set():
            r, _, _ = select([fd], [], [], self._SELECT_TIMEOUT_S)
            if r:
                for ev in dev.read():
                    if ev.type != self._ecodes.EV_KEY:
                        continue

                    kev = self._categorize(ev)
                    keycode = kev.keycode
                    if isinstance(keycode, list):
                        keycode = keycode[0]

                    token = _keycode_to_token(str(keycode))
                    if token is None:
                        continue

                    # keystate: 0=UP, 1=DOWN, 2=HOLD
                    if kev.keystate in (1, 2):
                        self._pressed.add(token)
                    elif kev.keystate == 0:
                        self._pressed.discard(token)

                    with self._lock:
                        self._last_key = token
                        self._last_bytes = b""  # not meaningful for evdev
                        self._last_read_t = monotonic()

                    # quit on DOWN
                    if kev.keystate == 1 and token in self._keys.quit:
                        self._quit.set()
                        break

                    # recompute motor immediately on any press/release affecting motor keys
                    if token in motor_tokens:
                        self._recompute_motor()

                    # servo: if a servo key changes, apply one immediate step so it feels responsive
                    if token in servo_tokens:
                        self._step_servo_from_pressed()

            # periodic motor refresh (beats deadman while held)
            now = monotonic()
            if (now - last_motor_refresh_t) >= self._MOTOR_REFRESH_S:
                if self._pressed.intersection(motor_tokens):
                    self._recompute_motor(refresh_only=True)
                last_motor_refresh_t = now

            # periodic servo stepping while held (supports 2-axis combos)
            if (now - last_servo_step_t) >= self._SERVO_STEP_PERIOD_S:
                if self._pressed.intersection(servo_tokens):
                    self._step_servo_from_pressed()
                last_servo_step_t = now

    # -------- motor/servo logic --------

    def _motor_tokens(self) -> set[str]:
        km = self._keys
        return (
            _as_set(km.motor_forward)
            | _as_set(km.motor_backward)
            | _as_set(km.motor_left)
            | _as_set(km.motor_right)
            | _as_set(km.motor_fwd_left)
            | _as_set(km.motor_fwd_right)
            | _as_set(km.motor_back_left)
            | _as_set(km.motor_back_right)
            | _as_set(km.motor_stop)
        )

    def _servo_tokens(self) -> set[str]:
        km = self._keys
        return (
            _as_set(km.servo_pan_left)
            | _as_set(km.servo_pan_right)
            | _as_set(km.servo_tilt_up)
            | _as_set(km.servo_tilt_down)
            | _as_set(km.servo_center)
        )

    def _recompute_motor(self, *, refresh_only: bool = False) -> None:
        km = self._keys
        pressed = self._pressed

        if pressed.intersection(km.motor_stop):
            self._set_motor(0, 0, refresh_only=refresh_only)
            return

        speed = int(self._cfg.speed)
        steer = int(self._cfg.steer)

        # prefer explicit diagonals if present
        if pressed.intersection(km.motor_fwd_right):
            self._set_motor(speed, steer, refresh_only=refresh_only)
            return
        if pressed.intersection(km.motor_fwd_left):
            self._set_motor(speed, -steer, refresh_only=refresh_only)
            return
        if pressed.intersection(km.motor_back_right):
            self._set_motor(-speed, -steer, refresh_only=refresh_only)
            return
        if pressed.intersection(km.motor_back_left):
            self._set_motor(-speed, steer, refresh_only=refresh_only)
            return

        throttle = 0
        steer_val = 0

        if pressed.intersection(km.motor_forward):
            throttle += speed
        if pressed.intersection(km.motor_backward):
            throttle -= speed

        if pressed.intersection(km.motor_right):
            steer_val += steer
        if pressed.intersection(km.motor_left):
            steer_val -= steer

        # if nothing is held, do nothing and let deadman stop it
        if throttle == 0 and steer_val == 0:
            return

        self._set_motor(throttle, steer_val, refresh_only=refresh_only)

    def _set_motor(
        self, throttle: int, steer_differential: int, *, refresh_only: bool = False
    ) -> None:
        steer = -steer_differential if self._cfg.invert_steer else steer_differential
        with self._lock:
            # Always refresh timestamp while held.
            # refresh_only exists so callers can keep logic stable; we still update ts.
            self._latest_motor = MotorCommand.now(throttle, steer)
            self._last_motor_input_t = monotonic()

    def _step_servo_from_pressed(self) -> None:
        km = self._keys
        pressed = self._pressed

        step = int(self._cfg.servo_step)
        pan_sign = -1 if self._cfg.invert_pan else 1
        tilt_sign = -1 if self._cfg.invert_tilt else 1

        pan = self._pan
        tilt = self._tilt
        changed = False

        # center wins over everything while held
        if pressed.intersection(km.servo_center):
            if pan != 0 or tilt != 0:
                pan = 0
                tilt = 0
                changed = True
        else:
            if pressed.intersection(km.servo_pan_left):
                pan -= step * pan_sign
                changed = True
            if pressed.intersection(km.servo_pan_right):
                pan += step * pan_sign
                changed = True
            if pressed.intersection(km.servo_tilt_up):
                tilt += step * tilt_sign
                changed = True
            if pressed.intersection(km.servo_tilt_down):
                tilt -= step * tilt_sign
                changed = True

        if changed:
            self._pan = pan
            self._tilt = tilt
            self._set_servo(self._pan, self._tilt)

    def _set_servo(self, pan: int, tilt: int) -> None:
        with self._lock:
            self._latest_servo = ServoCommand.now(pan, tilt)