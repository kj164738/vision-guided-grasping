import numpy as np
import pytest

pytest.importorskip("cv2")

from yolo_world_ros.detector import Detection
from yolo_world_ros.visualization import draw_detections


def test_draw_detections_preserves_shape_and_changes_pixels():
    image = np.zeros((80, 120, 3), dtype=np.uint8)
    detections = [Detection((10.0, 10.0, 50.0, 40.0), 0, "cup", 0.9)]

    annotated = draw_detections(image, detections)

    assert annotated.shape == image.shape
    assert np.any(annotated != image)
