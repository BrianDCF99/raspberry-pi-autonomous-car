from __future__ import annotations

from dataclasses import dataclass
from time import time

from carbot.config.models import ServoConfig
from carbot.contracts.servo_controller import Axis, ServoController


@dataclass(slots=True)
class ServoState:
    requested_relative: int
    clamped_relative: int
    logical: int
    physical: int
    timestamp: float


@dataclass(frozen=True, slots=True)
class RelativeLimits:
    pan_min: int
    pan_max: int
    tilt_min: int
    tilt_max: int


class ServoDriver:
    def __init__(self, controller: ServoController, cfg: ServoConfig) -> None:
        self._controller = controller
        self._cfg = cfg

        self._state: dict[Axis, ServoState] = {
            Axis.PAN: ServoState(0, 0, 0, 0, 0.0),
            Axis.TILT: ServoState(0, 0, 0, 0, 0.0),
        }

        self._relative_limits = RelativeLimits(
            pan_min=cfg.pan_min - cfg.pan_offset - cfg.pan_center,
            pan_max=cfg.pan_max - cfg.pan_offset - cfg.pan_center,
            tilt_min=cfg.tilt_min - cfg.tilt_offset - cfg.tilt_center,
            tilt_max=cfg.tilt_max - cfg.tilt_offset - cfg.tilt_center,
        )

        self.center()

    def close(self) -> None:
        self.center()
        self._controller.close()

    def center(self) -> None:
        self.set_pan(0)
        self.set_tilt(0)

    def set_pan(self, relative_angle: int) -> None:
        self._set_relative(Axis.PAN, relative_angle)

    def set_tilt(self, relative_angle: int) -> None:
        self._set_relative(Axis.TILT, relative_angle)

    @property
    def curr_pan_angle(self) -> int:
        return self._state[Axis.PAN].clamped_relative

    @property
    def curr_tilt_angle(self) -> int:
        return self._state[Axis.TILT].clamped_relative

    def _set_relative(self, axis: Axis, relative: int) -> None:
        clamped_relative = self._clamp_relative(axis, relative)
        logical = clamped_relative + self._center(axis)
        physical = self._clamp_physical(axis, logical + self._offset(axis))

        self._controller.set_angle(axis, physical)
        self._state[axis] = ServoState(
            relative, clamped_relative, logical, physical, time()
        )

    def _center(self, axis: Axis) -> int:
        if axis == Axis.PAN:
            return self._cfg.pan_center

        return self._cfg.tilt_center

    def _offset(self, axis: Axis) -> int:
        if axis == Axis.PAN:
            return self._cfg.pan_offset

        return self._cfg.tilt_offset

    def _clamp_relative(self, axis: Axis, relative: int) -> int:
        if axis == Axis.PAN:
            lower = self._relative_limits.pan_min
            upper = self._relative_limits.pan_max
        else:
            lower = self._relative_limits.tilt_min
            upper = self._relative_limits.tilt_max

        return max(lower, min(relative, upper))

    def _clamp_physical(self, axis: Axis, physical: int) -> int:
        if axis == Axis.PAN:
            lower = self._cfg.pan_min
            upper = self._cfg.pan_max
        else:
            lower = self._cfg.tilt_min
            upper = self._cfg.tilt_max

        return max(lower, min(physical, upper))
