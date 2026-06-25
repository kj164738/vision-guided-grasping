import numpy as np
import pytest

from yolo_world_ros.detector import (
    MockDetector,
    labels_to_yolo_world_texts,
    parse_text_prompt,
)


def test_parse_text_prompt_strips_empty_labels():
    assert parse_text_prompt(" cup, , bottle ,box ") == ["cup", "bottle", "box"]


def test_parse_text_prompt_rejects_empty_input():
    with pytest.raises(ValueError, match="text_prompt"):
        parse_text_prompt(" , ")


def test_labels_to_yolo_world_texts_adds_background_prompt():
    assert labels_to_yolo_world_texts(["cup", "box"]) == [["cup"], ["box"], [" "]]


def test_mock_detector_returns_centered_detection():
    detector = MockDetector(["cup"])
    image = np.zeros((100, 200, 3), dtype=np.uint8)

    detections = detector.detect(image)

    assert len(detections) == 1
    detection = detections[0]
    assert detection.label == "cup"
    assert detection.class_id == 0
    assert detection.score == pytest.approx(0.99)
    assert detection.xyxy == pytest.approx((60.0, 30.0, 140.0, 70.0))
