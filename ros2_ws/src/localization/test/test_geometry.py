import math

import pytest

from localization.geometry import (
    CameraIntrinsics,
    PixelPoint,
    Point3D,
    Quaternion,
    Transform3D,
    back_project_pixel,
    transform_point,
)


def test_back_project_pixel_uses_pinhole_camera_model():
    intrinsics = CameraIntrinsics(fx=500.0, fy=250.0, cx=320.0, cy=240.0)

    point = back_project_pixel(PixelPoint(420.0, 290.0), 2.0, intrinsics)

    assert point.x == pytest.approx(0.4)
    assert point.y == pytest.approx(0.4)
    assert point.z == pytest.approx(2.0)


def test_transform_point_applies_rotation_and_translation():
    angle = math.pi / 2.0
    transform = Transform3D(
        translation=Point3D(1.0, 2.0, 3.0),
        rotation=Quaternion(0.0, 0.0, math.sin(angle / 2.0), math.cos(angle / 2.0)),
    )

    point = transform_point(Point3D(1.0, 0.0, 0.0), transform)

    assert point.x == pytest.approx(1.0)
    assert point.y == pytest.approx(3.0)
    assert point.z == pytest.approx(3.0)
