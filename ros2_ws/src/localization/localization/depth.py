from __future__ import annotations

import math

import numpy as np

from localization.geometry import PixelPoint


def depth_image_to_meters(depth_image: np.ndarray, encoding: str) -> np.ndarray:
    if encoding == "16UC1" or depth_image.dtype == np.uint16:
        return depth_image.astype(np.float32) * 0.001
    if encoding == "32FC1" or np.issubdtype(depth_image.dtype, np.floating):
        return depth_image.astype(np.float32)
    raise ValueError(f"Unsupported depth image encoding: {encoding}")


def median_depth_near_pixel(
    depth_m: np.ndarray,
    pixel: PixelPoint,
    window_size: int,
    min_depth_m: float,
    max_depth_m: float,
) -> float | None:
    if depth_m.ndim != 2:
        raise ValueError("depth_m must be a single-channel image")
    if window_size < 1:
        raise ValueError("window_size must be positive")

    height, width = depth_m.shape
    center_u = int(round(pixel.u))
    center_v = int(round(pixel.v))
    if center_u < 0 or center_u >= width or center_v < 0 or center_v >= height:
        return None

    radius = window_size // 2
    u1 = max(center_u - radius, 0)
    u2 = min(center_u + radius + 1, width)
    v1 = max(center_v - radius, 0)
    v2 = min(center_v + radius + 1, height)
    window = depth_m[v1:v2, u1:u2]

    valid = window[np.isfinite(window)]
    valid = valid[(valid >= min_depth_m) & (valid <= max_depth_m)]
    valid = valid[valid > 0.0]
    if valid.size == 0:
        return None

    depth = float(np.median(valid))
    if not math.isfinite(depth):
        return None
    return depth
