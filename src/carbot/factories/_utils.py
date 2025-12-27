from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TypeVar

T = TypeVar("T")


def resolve_factory(
    registry: Mapping[str, Callable[..., T]],
    key: str,
    *,
    registry_name: str,
) -> Callable[..., T]:
    """
    Lookup a factory in a registry and raise a clean ValueError on invalid keys.
    """
    try:
        return registry[key]
    except KeyError as e:
        allowed = ", ".join(sorted(registry))
        raise ValueError(
            f"Unknown {registry_name} key: {key!r}. Allowed: {allowed}"
        ) from e
