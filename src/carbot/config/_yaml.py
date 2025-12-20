from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping


def resolve_config_path(
    name_or_path: str | Path,
    *,
    config_dir: str | Path,
    default_ext: str = ".yaml",
) -> Path:
    base = Path(config_dir)
    p = Path(name_or_path)

    # If it looks like a path (has dirs) or has an extension, treat it as a path.
    if p.parent != Path(".") or p.suffix:
        path = p if p.is_absolute() else (Path.cwd() / p)
    else:
        path = base / f"{p}{default_ext}"

    return path.resolve()


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    import yaml

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(
            f"Invalid YAML in {path}: expected mapping/object at top-level"
        )
    return data


def require_key(data: Mapping[str, Any], key: str, *, path: Path) -> Any:
    if key not in data:
        raise ValueError(f"Missing required key {key!r} in {path}")
    return data[key]


def forbid_unknown_keys(
    data: Mapping[str, Any], allowed: set[str], *, path: Path
) -> None:
    unknown = set(data.keys()) - allowed
    if unknown:
        raise ValueError(f"Unknown keys in {path}: {sorted(unknown)}")


def as_int(x: Any, *, key: str, path: Path) -> int:
    try:
        return int(x)
    except Exception as e:
        raise ValueError(f"Key {key!r} in {path} must be int; got {x!r}") from e


def as_float(x: Any, *, key: str, path: Path) -> float:
    try:
        return float(x)
    except Exception as e:
        raise ValueError(f"Key {key!r} in {path} must be float; got {x!r}") from e
