from __future__ import annotations

import threading
from dataclasses import dataclass
from time import monotonic, sleep
from typing import Optional, Protocol

from carbot.control.commands import MotorCommand, ServoCommand
from carbot.control.mux import PriorityMux


class MotorSink(Protocol):
    def drive(self, throttle: int, steer_differential: int) -> None: ...


class ServoSink(Protocol):
    def set_pan(self, relative_angle: int) -> None: ...
    def set_tilt(self, relative_angle: int) -> None: ...
    def center(self) -> None: ...


@dataclass(frozen=True, slots=True)
class ControlLoopConfig:
    hz: float = 50.0
    idle_sleep_s: float = 0.002


class ControlLoop:
    def __init__(
        self,
        *,
        cfg: ControlLoopConfig,
        motor: Optional[MotorSink],
        servo: Optional[ServoSink],
        motor_mux: Optional[PriorityMux[MotorCommand]] = None,
        servo_mux: Optional[PriorityMux[ServoCommand]] = None,
        motor_failsafe_stop: bool = True,
    ) -> None:
        self._cfg = cfg
        self._motor = motor
        self._servo = servo
        self._motor_mux = motor_mux
        self._servo_mux = servo_mux
        self._motor_failsafe_stop = motor_failsafe_stop

        self._stop = threading.Event()

        self._last_motor: tuple[int, int] | None = None
        self._last_servo: tuple[int, int] | None = None

    def stop(self) -> None:
        self._stop.set()

    def run_forever(self) -> None:
        hz = float(self._cfg.hz)
        interval = (1.0 / hz) if hz > 0 else float(self._cfg.idle_sleep_s)

        next_t = monotonic()
        while not self._stop.is_set():
            self.tick()

            next_t += interval
            delay = next_t - monotonic()
            if delay > 0:
                sleep(delay)
            else:
                next_t = monotonic()
                sleep(float(self._cfg.idle_sleep_s))

        if self._motor is not None and self._motor_failsafe_stop:
            try:
                self._motor.drive(0, 0)
            except Exception:
                pass

    def tick(self) -> None:
        # MOTOR
        if self._motor is not None and self._motor_mux is not None:
            cmd = self._motor_mux.pick()
            if cmd is None:
                cmd = MotorCommand.stop() if self._motor_failsafe_stop else None

            if cmd is not None:
                pair = (cmd.throttle, cmd.steer_differential)
                if pair != self._last_motor:
                    self._motor.drive(cmd.throttle, cmd.steer_differential)
                    self._last_motor = pair

        # SERVO
        if self._servo is not None and self._servo_mux is not None:
            scmd = self._servo_mux.pick()
            if scmd is not None:
                pair = (scmd.pan, scmd.tilt)
                if pair != self._last_servo:
                    self._servo.set_pan(scmd.pan)
                    self._servo.set_tilt(scmd.tilt)
                    self._last_servo = pair