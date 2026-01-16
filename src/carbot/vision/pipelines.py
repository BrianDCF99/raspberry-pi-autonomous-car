from __future__ import annotations

from collections.abc import Callable

import cv2 as cv
import numpy as np

FrameTransform = Callable[[np.ndarray], np.ndarray]


def identity(img_bgr: np.ndarray) -> np.ndarray:
    return img_bgr


def crop_bottom_quarter(img_bgr: np.ndarray) -> np.ndarray:
    h, _w = img_bgr.shape[:2]
    return img_bgr[h // 4 :, :]


def canny_bottom_quarter(img_bgr: np.ndarray, *, t1: int = 75, t2: int = 150) -> np.ndarray:
    cropped = crop_bottom_quarter(img_bgr)
    gray = cv.cvtColor(cropped, cv.COLOR_BGR2GRAY)
    return cv.Canny(gray, t1, t2)