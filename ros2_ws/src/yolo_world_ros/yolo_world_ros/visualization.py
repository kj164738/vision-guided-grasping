from __future__ import annotations

import cv2
import numpy as np

from yolo_world_ros.detector import Detection


def draw_detections(bgr_image: np.ndarray, detections: list[Detection]) -> np.ndarray:
    annotated = bgr_image.copy()
    for detection in detections:
        x1, y1, x2, y2 = [int(round(value)) for value in detection.xyxy]
        label = f"{detection.label} {detection.score:.2f}"
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 180, 0), 2)
        _draw_label(annotated, label, x1, y1)
    return annotated


def _draw_label(image: np.ndarray, label: str, x: int, y: int) -> None:
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.5
    thickness = 1
    text_size, baseline = cv2.getTextSize(label, font, scale, thickness)
    text_width, text_height = text_size
    top = max(y - text_height - baseline - 4, 0)
    bottom = top + text_height + baseline + 4
    right = min(x + text_width + 6, image.shape[1] - 1)
    cv2.rectangle(image, (x, top), (right, bottom), (0, 180, 0), -1)
    cv2.putText(
        image,
        label,
        (x + 3, bottom - baseline - 2),
        font,
        scale,
        (255, 255, 255),
        thickness,
        cv2.LINE_AA,
    )
