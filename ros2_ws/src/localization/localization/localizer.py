from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from localization.depth import median_depth_near_pixel
from localization.geometry import CameraIntrinsics, PixelPoint, Point3D, back_project_pixel


@dataclass(frozen=True)
class Detection2DCenter:
    u: float
    v: float
    label: str
    score: float


@dataclass(frozen=True)
class LocalizedObject:
    point_camera: Point3D
    label: str
    score: float


def localize_detections(
    detections: list[Detection2DCenter],
    depth_m: np.ndarray,
    intrinsics: CameraIntrinsics,
    depth_window_size: int,
    min_depth_m: float,
    max_depth_m: float,
) -> list[LocalizedObject]:
    localized: list[LocalizedObject] = []
    for detection in detections:
        pixel = PixelPoint(u=detection.u, v=detection.v)
        depth = median_depth_near_pixel(
            depth_m=depth_m,
            pixel=pixel,
            window_size=depth_window_size,
            min_depth_m=min_depth_m,
            max_depth_m=max_depth_m,
        )
        if depth is None:
            continue

        localized.append(
            LocalizedObject(
                point_camera=back_project_pixel(pixel, depth, intrinsics),
                label=detection.label,
                score=detection.score,
            )
        )
    return localized
