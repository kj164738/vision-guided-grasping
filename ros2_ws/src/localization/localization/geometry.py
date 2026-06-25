from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class CameraIntrinsics:
    fx: float
    fy: float
    cx: float
    cy: float


@dataclass(frozen=True)
class PixelPoint:
    u: float
    v: float


@dataclass(frozen=True)
class Point3D:
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class Quaternion:
    x: float
    y: float
    z: float
    w: float


@dataclass(frozen=True)
class Transform3D:
    translation: Point3D
    rotation: Quaternion


def back_project_pixel(pixel: PixelPoint, depth_m: float, intrinsics: CameraIntrinsics) -> Point3D:
    if intrinsics.fx == 0.0 or intrinsics.fy == 0.0:
        raise ValueError("Camera intrinsics fx and fy must be non-zero")

    x = (pixel.u - intrinsics.cx) * depth_m / intrinsics.fx
    y = (pixel.v - intrinsics.cy) * depth_m / intrinsics.fy
    return Point3D(x=x, y=y, z=depth_m)


def transform_point(point: Point3D, transform: Transform3D) -> Point3D:
    rotated = _rotate_point(point, _normalize_quaternion(transform.rotation))
    return Point3D(
        x=rotated.x + transform.translation.x,
        y=rotated.y + transform.translation.y,
        z=rotated.z + transform.translation.z,
    )


def _normalize_quaternion(quaternion: Quaternion) -> Quaternion:
    norm = math.sqrt(
        quaternion.x * quaternion.x
        + quaternion.y * quaternion.y
        + quaternion.z * quaternion.z
        + quaternion.w * quaternion.w
    )
    if norm == 0.0:
        raise ValueError("Transform quaternion must be non-zero")
    return Quaternion(
        x=quaternion.x / norm,
        y=quaternion.y / norm,
        z=quaternion.z / norm,
        w=quaternion.w / norm,
    )


def _rotate_point(point: Point3D, quaternion: Quaternion) -> Point3D:
    qx, qy, qz, qw = quaternion.x, quaternion.y, quaternion.z, quaternion.w

    # Rotation matrix equivalent for q * p * q^-1.
    xx = qx * qx
    yy = qy * qy
    zz = qz * qz
    xy = qx * qy
    xz = qx * qz
    yz = qy * qz
    wx = qw * qx
    wy = qw * qy
    wz = qw * qz

    return Point3D(
        x=(1.0 - 2.0 * (yy + zz)) * point.x
        + 2.0 * (xy - wz) * point.y
        + 2.0 * (xz + wy) * point.z,
        y=2.0 * (xy + wz) * point.x
        + (1.0 - 2.0 * (xx + zz)) * point.y
        + 2.0 * (yz - wx) * point.z,
        z=2.0 * (xz - wy) * point.x
        + 2.0 * (yz + wx) * point.y
        + (1.0 - 2.0 * (xx + yy)) * point.z,
    )
