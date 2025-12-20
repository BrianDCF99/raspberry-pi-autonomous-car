from enum import Enum, auto
from typing import Protocol


class Axis(Enum):
    PAN = auto()
    TILT = auto()


class ServoController(Protocol):
    def set_angle(self, axis: Axis, angle: int) -> None: ...
    def close(self) -> None: ...
