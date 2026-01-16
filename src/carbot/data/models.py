from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from carbot.config.models import (
    CameraConfig,
    CameraPolicy,
    InfraredConfig,
    MotorConfig,
    NetworkConfig,
    ServoConfig,
    UltrasonicConfig,
)


@dataclass(frozen=True, slots=True)
class DataEntry:
    jpeg: bytes
    throttle: int
    steer: int
    pan: int
    tilt: int
    infrared: int | None
    ultrasonic: int | None
    ts: int


@dataclass(frozen=True, slots=True)
class Metadata:
    motor_cfg: MotorConfig | None
    servo_cfg: ServoConfig | None
    infra_cfg: InfraredConfig | None
    ultra_cfg: UltrasonicConfig | None
    cam_cfg: CameraConfig | None
    cam_policy: CameraPolicy | None
    network_cfg: NetworkConfig | None


class MetadataBuilder:
    def __init__(self) -> None:
        self.motor_cfg: MotorConfig | None = None
        self.servo_cfg: ServoConfig | None = None
        self.infra_cfg: InfraredConfig | None = None
        self.ultra_cfg: UltrasonicConfig | None = None
        self.cam_cfg: CameraConfig | None = None
        self.cam_policy: CameraPolicy | None = None
        self.network_cfg: NetworkConfig | None = None

    def set_motor_cfg(self, cfg: MotorConfig) -> None:
        self.motor_cfg = cfg

    def set_servo_cfg(self, cfg: ServoConfig) -> None:
        self.servo_cfg = cfg

    def set_infra_cfg(self, cfg: InfraredConfig) -> None:
        self.infra_cfg = cfg

    def set_ultra_cfg(self, cfg: UltrasonicConfig) -> None:
        self.ultra_cfg = cfg

    def set_cam_cfg(self, cfg: CameraConfig) -> None:
        self.cam_cfg = cfg

    def set_cam_policy(self, policy: CameraPolicy) -> None:
        self.cam_policy = policy

    def set_network_cfg(self, cfg: NetworkConfig) -> None:
        self.network_cfg = cfg

    def build(self) -> Metadata:
        # If you want strict requirements, enforce them here.
        # Example: if cam_cfg is required for recording, raise if None.
        return Metadata(
            motor_cfg=self.motor_cfg,
            servo_cfg=self.servo_cfg,
            infra_cfg=self.infra_cfg,
            ultra_cfg=self.ultra_cfg,
            cam_cfg=self.cam_cfg,
            cam_policy=self.cam_policy,
            network_cfg=self.network_cfg,
        )