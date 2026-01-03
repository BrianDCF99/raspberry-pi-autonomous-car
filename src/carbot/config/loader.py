from __future__ import annotations

from pathlib import Path

from ._yaml import load_yaml_mapping, resolve_config_path
from .models import (
    CameraConfig,
    CameraPolicy,
    InfraredConfig,
    MotorConfig,
    NetworkConfig,
    RunConfig,
    ServoConfig,
    UltrasonicConfig,
    TeleopConfig,
)

_CONFIGS_DIR = Path(__file__).resolve().parents[3] / "configs"


def load_motor_config(
    name_or_path: str | Path, *, config_dir: str | Path | None = None
) -> MotorConfig:
    base = Path(config_dir) if config_dir is not None else (_CONFIGS_DIR / "motors")
    path = resolve_config_path(name_or_path, config_dir=base)
    data = load_yaml_mapping(path)
    return MotorConfig.from_mapping(data, path=path)


def load_servo_config(
    name_or_path: str | Path, *, config_dir: str | Path | None = None
) -> ServoConfig:
    base = Path(config_dir) if config_dir is not None else (_CONFIGS_DIR / "servos")
    path = resolve_config_path(name_or_path, config_dir=base)
    data = load_yaml_mapping(path)
    return ServoConfig.from_mapping(data, path=path)


def load_infrared_config(
    name_or_path: str | Path, *, config_dir: str | Path | None = None
) -> InfraredConfig:
    base = Path(config_dir) if config_dir is not None else (_CONFIGS_DIR / "infrared")
    path = resolve_config_path(name_or_path, config_dir=base)
    data = load_yaml_mapping(path)
    return InfraredConfig.from_mapping(data, path=path)


def load_ultrasonic_config(
    name_or_path: str | Path, *, config_dir: str | Path | None = None
) -> UltrasonicConfig:
    base = Path(config_dir) if config_dir is not None else (_CONFIGS_DIR / "ultrasonic")
    path = resolve_config_path(name_or_path, config_dir=base)
    data = load_yaml_mapping(path)
    return UltrasonicConfig.from_mapping(data, path=path)


def load_camera_config(
    name_or_path: str | Path, *, config_dir: str | Path | None = None
) -> CameraConfig:
    base = Path(config_dir) if config_dir is not None else (_CONFIGS_DIR / "camera")
    path = resolve_config_path(name_or_path, config_dir=base)
    data = load_yaml_mapping(path)
    return CameraConfig.from_mapping(data, path=path)


def load_camera_policy(
    name_or_path: str | Path, *, config_dir: str | Path | None = None
) -> CameraPolicy:
    base = Path(config_dir) if config_dir is not None else (_CONFIGS_DIR / "camera")
    path = resolve_config_path(name_or_path, config_dir=base)
    data = load_yaml_mapping(path)
    return CameraPolicy.from_mapping(data, path=path)


def load_network_config(
    name_or_path: str | Path, *, config_dir: str | Path | None = None
) -> NetworkConfig:
    base = Path(config_dir) if config_dir is not None else (_CONFIGS_DIR / "networking")
    path = resolve_config_path(name_or_path, config_dir=base)
    data = load_yaml_mapping(path)
    return NetworkConfig.from_mapping(data, path=path)

def load_teleop_config(
    name_or_path: str | Path, *, config_dir: str | Path | None = None
) -> TeleopConfig:
    base = Path(config_dir) if config_dir is not None else (_CONFIGS_DIR / "teleop")
    path = resolve_config_path(name_or_path, config_dir=base)
    data = load_yaml_mapping(path)
    return TeleopConfig.from_mapping(data, path=path)

def load_run_config(
    name_or_path: str | Path, *, config_dir: str | Path | None = None
) -> RunConfig:
    base = Path(config_dir) if config_dir is not None else (_CONFIGS_DIR / "run")
    path = resolve_config_path(name_or_path, config_dir=base)
    data = load_yaml_mapping(path)
    return RunConfig.from_mapping(data, path=path)
