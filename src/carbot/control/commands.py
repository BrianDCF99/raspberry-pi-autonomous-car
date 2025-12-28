from __future__ import annotations

from dataclasses import dataclass
from time import monotonic


@dataclass(frozen=True, slots=True)
class MotorCommand:
    throttle: int
    steer_differential: int
    ts: float

    @staticmethod
    def now(throttle: int, steer_differential: int) -> "MotorCommand":
        return MotorCommand(
            throttle=int(throttle),
            steer_differential=int(steer_differential),
            ts=monotonic(),
        )

    @staticmethod
    def stop() -> "MotorCommand":
        return MotorCommand(throttle=0, steer_differential=0, ts=monotonic())


@dataclass(frozen=True, slots=True)
class ServoCommand:
    pan: int
    tilt: int
    ts: float

    @staticmethod
    def now(pan: int, tilt: int) -> "ServoCommand":
        return ServoCommand(pan=int(pan), tilt=int(tilt), ts=monotonic())