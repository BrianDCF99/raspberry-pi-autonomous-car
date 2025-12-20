from __future__ import annotations

from pathlib import Path

from ._yaml import load_yaml_mapping, resolve_config_path
from .models import MotorConfig, ServoConfig


def load_motor_config(
    name_or_path: str | Path,
    *,
    config_dir: str | Path | None = None,
) -> MotorConfig:
    base = (
        Path(config_dir)
        if config_dir is not None
        else (Path.cwd() / "configs" / "motors")
    )
    path = resolve_config_path(name_or_path, config_dir=base)
    data = load_yaml_mapping(path)
    return MotorConfig.from_mapping(data, path=path)


def load_servo_config(
    name_or_path: str | Path,
    *,
    config_dir: str | Path | None = None,
) -> ServoConfig:
    base = (
        Path(config_dir)
        if config_dir is not None
        else (Path.cwd() / "configs" / "servos")
    )
    path = resolve_config_path(name_or_path, config_dir=base)
    data = load_yaml_mapping(path)
    return ServoConfig.from_mapping(data, path=path)
