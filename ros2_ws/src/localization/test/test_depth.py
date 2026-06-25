import numpy as np
import pytest

from localization.depth import depth_image_to_meters, median_depth_near_pixel
from localization.geometry import PixelPoint


def test_16uc1_depth_is_converted_from_millimeters_to_meters():
    depth = np.array([[0, 500], [1000, 1500]], dtype=np.uint16)

    converted = depth_image_to_meters(depth, "16UC1")

    assert converted.dtype == np.float32
    np.testing.assert_allclose(converted, np.array([[0.0, 0.5], [1.0, 1.5]], dtype=np.float32))


def test_32fc1_depth_keeps_meter_units():
    depth = np.array([[0.1, 1.25]], dtype=np.float32)

    converted = depth_image_to_meters(depth, "32FC1")

    assert converted.dtype == np.float32
    assert converted.tolist() == [[pytest.approx(0.1), pytest.approx(1.25)]]


def test_median_depth_uses_valid_values_inside_window():
    depth = np.array(
        [
            [0.0, 0.1, 0.2],
            [0.3, 1.0, 4.0],
            [np.nan, 1.2, 1.4],
        ],
        dtype=np.float32,
    )

    result = median_depth_near_pixel(
        depth_m=depth,
        pixel=PixelPoint(1.0, 1.0),
        window_size=3,
        min_depth_m=0.2,
        max_depth_m=2.0,
    )

    assert result == pytest.approx(1.0)


def test_median_depth_returns_none_when_pixel_is_outside_image():
    depth = np.ones((3, 3), dtype=np.float32)

    result = median_depth_near_pixel(
        depth_m=depth,
        pixel=PixelPoint(10.0, 1.0),
        window_size=3,
        min_depth_m=0.1,
        max_depth_m=2.0,
    )

    assert result is None


def test_median_depth_returns_none_when_all_values_invalid():
    depth = np.zeros((3, 3), dtype=np.float32)

    result = median_depth_near_pixel(
        depth_m=depth,
        pixel=PixelPoint(1.0, 1.0),
        window_size=3,
        min_depth_m=0.1,
        max_depth_m=2.0,
    )

    assert result is None
