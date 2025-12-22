from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True, slots=True)
class BGRFrame:
    img: np.ndarray  # BGR uint8 HxWx3 (OpenCV-ready)
    timestamp: int


class CameraController(Protocol):
    def try_read_frame(self) -> BGRFrame | None: ...
    def close(self) -> None: ...
