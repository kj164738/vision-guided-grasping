import numpy as np
import pytest

from localization.geometry import CameraIntrinsics
from localization.localizer import Detection2DCenter, localize_detections


def test_localize_detections_back_projects_valid_detection():
    depth = np.ones((5, 5), dtype=np.float32) * 2.0
    intrinsics = CameraIntrinsics(fx=100.0, fy=100.0, cx=2.0, cy=2.0)
    detections = [Detection2DCenter(u=3.0, v=4.0, label="cup", score=0.9)]

    localized = localize_detections(
        detections=detections,
        depth_m=depth,
        intrinsics=intrinsics,
        depth_window_size=3,
        min_depth_m=0.05,
        max_depth_m=3.0,
    )

    assert len(localized) == 1
    assert localized[0].label == "cup"
    assert localized[0].score == pytest.approx(0.9)
    assert localized[0].point_camera.x == pytest.approx(0.02)
    assert localized[0].point_camera.y == pytest.approx(0.04)
    assert localized[0].point_camera.z == pytest.approx(2.0)


def test_localize_detections_skips_empty_or_invalid_depth():
    depth = np.zeros((5, 5), dtype=np.float32)
    intrinsics = CameraIntrinsics(fx=100.0, fy=100.0, cx=2.0, cy=2.0)
    detections = [Detection2DCenter(u=2.0, v=2.0, label="cup", score=0.9)]

    localized = localize_detections(
        detections=detections,
        depth_m=depth,
        intrinsics=intrinsics,
        depth_window_size=3,
        min_depth_m=0.05,
        max_depth_m=3.0,
    )

    assert localized == []
