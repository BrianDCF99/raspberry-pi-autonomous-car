from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from ._yaml import as_float, as_int, forbid_unknown_keys, require_key


@dataclass(frozen=True, slots=True)
class MotorConfig:
    max_power: int
    left_scale: float = 1.0
    right_scale: float = 1.0

    @staticmethod
    def from_mapping(data: Mapping[str, Any], *, path: Path) -> "MotorConfig":
        allowed = {"max_power", "left_scale", "right_scale"}
        forbid_unknown_keys(data, allowed, path=path)

        max_power = as_int(
            require_key(data, "max_power", path=path), key="max_power", path=path
        )
        left_scale = as_float(data.get("left_scale", 1.0), key="left_scale", path=path)
        right_scale = as_float(
            data.get("right_scale", 1.0), key="right_scale", path=path
        )

        return MotorConfig(
            max_power=max_power, left_scale=left_scale, right_scale=right_scale
        )


@dataclass(frozen=True, slots=True)
class ServoConfig:
    pan_center: int
    tilt_center: int

    pan_min: int
    pan_max: int
    tilt_min: int
    tilt_max: int

    pan_offset: int = 0
    tilt_offset: int = 0

    @staticmethod
    def from_mapping(data: Mapping[str, Any], *, path: Path) -> "ServoConfig":
        allowed = {
            "pan_center",
            "tilt_center",
            "pan_min",
            "pan_max",
            "tilt_min",
            "tilt_max",
            "pan_offset",
            "tilt_offset",
        }
        forbid_unknown_keys(data, allowed, path=path)

        def req_int(k: str) -> int:
            return as_int(require_key(data, k, path=path), key=k, path=path)

        return ServoConfig(
            pan_center=req_int("pan_center"),
            tilt_center=req_int("tilt_center"),
            pan_min=req_int("pan_min"),
            pan_max=req_int("pan_max"),
            tilt_min=req_int("tilt_min"),
            tilt_max=req_int("tilt_max"),
            pan_offset=as_int(data.get("pan_offset", 0), key="pan_offset", path=path),
            tilt_offset=as_int(
                data.get("tilt_offset", 0), key="tilt_offset", path=path
            ),
        )
