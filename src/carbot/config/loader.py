from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import MotorConfig


def load_motor_config(name_or_path: str | Path, *, config_dir: str | Path | None = None) -> MotorConfig:
    """
    Accepts either:
      - "slow_car"  -> resolves to <config_dir>/slow_car.yaml
      - "configs/slow_car.yaml" (relative) or "/abs/path/slow_car.yaml" (absolute)
    """
    config_base = Path(config_dir) if config_dir is not None else Path.cwd() / "configs"
    p = Path(name_or_path)

    # If it looks like a path (has parent dirs) or ends with .yaml, use it as a path.
    if p.suffix == ".yaml" or p.parent != Path("."):
        path = p if p.is_absolute() else (Path.cwd() / p)
    else:
        # Treat it as a short name.
        path = config_base / f"{p}.yaml"

    path = path.resolve()

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML in {path}: expected a mapping/object at top-level")

    max_power_raw = data.get("max_power")
    if max_power_raw is None:
        raise ValueError(f"Missing required key 'max_power' in {path}")

    return MotorConfig(
        name=str(data.get("name", path.stem)),
        max_power=int(max_power_raw),
        left_scale=float(data.get("left_scale", 1.0)),
        right_scale=float(data.get("right_scale", 1.0)),
    )