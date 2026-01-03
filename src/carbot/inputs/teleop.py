# carbot/inputs/teleop.py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable

from carbot.config.models import TeleopConfig
from carbot.config.models import TeleopKeymap
from carbot.control.commands import MotorCommand, ServoCommand
from carbot.control.mux import Source


_REVERSE_KEY_ALIASES: dict[str, str] = {
    "\x1b[A": "UP",
    "\x1b[B": "DOWN",
    "\x1b[C": "RIGHT",
    "\x1b[D": "LEFT",
    " ": "SPACE",
    "\r": "ENTER",
    "\t": "TAB",
    "\x1b": "ESC",
    "\x03": "CTRL_C",
}


def _fmt_keys(keys: list[str]) -> str:
    out: list[str] = []
    for k in keys:
        alias = _REVERSE_KEY_ALIASES.get(k)
        if alias is not None:
            out.append(alias)
            continue

        if len(k) == 1 and k.isprintable():
            out.append(k)
            continue

        out.append(k.encode("utf-8", "backslashreplace").decode("utf-8"))

    return " / ".join(out) if out else "—"


class Teleop(Source[MotorCommand], ABC):
    """
    Teleop = "something that emits MotorCommand + ServoCommand".
    Hardware-agnostic: no drivers touched here, only commands produced.
    """

    @property
    @abstractmethod
    def keymap(self) -> TeleopKeymap: ...

    @property
    @abstractmethod
    def quit_requested(self) -> bool: ...

    @property
    @abstractmethod
    def alive(self) -> bool: ...

    @property
    @abstractmethod
    def cfg(self) -> TeleopConfig: ...

    @abstractmethod
    def start(self) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...

    def close(self) -> None:
        self.stop()

    @abstractmethod
    def thread_error(self) -> BaseException | None: ...

    @abstractmethod
    def debug_last_key(self) -> tuple[str | None, bytes, float]: ...

    @abstractmethod
    def latest_motor(self) -> MotorCommand | None: ...

    @abstractmethod
    def latest_servo(self) -> ServoCommand | None: ...

    # Source[MotorCommand]
    def latest(self) -> MotorCommand | None:
        return self.latest_motor()

    def help_text(self, *, teleop_cfg_name: str | None = None) -> str:
        km = self.keymap
        header = "\n=== TELEOP CONTROLS ===\n"
        if teleop_cfg_name:
            header += f"teleop config: {teleop_cfg_name}\n"
        header += "\n"

        return (
            header
            + "Motor:\n"
            + f"  forward:    {_fmt_keys(km.motor_forward)}\n"
            + f"  backward:   {_fmt_keys(km.motor_backward)}\n"
            + f"  left:       {_fmt_keys(km.motor_left)}\n"
            + f"  right:      {_fmt_keys(km.motor_right)}\n"
            + f"  fwd-left:   {_fmt_keys(km.motor_fwd_left)}\n"
            + f"  fwd-right:  {_fmt_keys(km.motor_fwd_right)}\n"
            + f"  back-left:  {_fmt_keys(km.motor_back_left)}\n"
            + f"  back-right: {_fmt_keys(km.motor_back_right)}\n"
            + f"  stop:       {_fmt_keys(km.motor_stop)}\n"
            + "\nServo:\n"
            + f"  pan left:   {_fmt_keys(km.servo_pan_left)}\n"
            + f"  pan right:  {_fmt_keys(km.servo_pan_right)}\n"
            + f"  tilt up:    {_fmt_keys(km.servo_tilt_up)}\n"
            + f"  tilt down:  {_fmt_keys(km.servo_tilt_down)}\n"
            + f"  center:     {_fmt_keys(km.servo_center)}\n"
            + "\nQuit:\n"
            + f"  quit:       {_fmt_keys(km.quit)}\n"
            + "\nNote: input method may run without echo / in raw mode depending on teleop.\n"
        )


@dataclass(frozen=True, slots=True)
class MotorSource(Source[MotorCommand]):
    teleop: Teleop

    def latest(self) -> MotorCommand | None:
        return self.teleop.latest_motor()


@dataclass(frozen=True, slots=True)
class ServoSource(Source[ServoCommand]):
    teleop: Teleop

    def latest(self) -> ServoCommand | None:
        return self.teleop.latest_servo()