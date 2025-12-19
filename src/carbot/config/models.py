from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class MotorConfig:
    name: str
    max_power: int
    left_scale: float = 1.0
    right_scale: float = 1.0