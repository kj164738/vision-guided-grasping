from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class Detection:
    """Model-agnostic detection result in pixel coordinates."""

    xyxy: tuple[float, float, float, float]
    class_id: int
    label: str
    score: float


class Detector(Protocol):
    def detect(self, bgr_image: np.ndarray) -> list[Detection]:
        """Return detections for an OpenCV BGR image."""


def parse_text_prompt(text_prompt: str) -> list[str]:
    labels = [label.strip() for label in text_prompt.split(",") if label.strip()]
    if not labels:
        raise ValueError("text_prompt must contain at least one non-empty label")
    return labels


def labels_to_yolo_world_texts(labels: list[str]) -> list[list[str]]:
    return [[label] for label in labels] + [[" "]]


class MockDetector:
    """Deterministic detector for ROS topic and visualization debugging."""

    def __init__(self, labels: list[str], score: float = 0.99) -> None:
        self._labels = labels
        self._score = score

    def detect(self, bgr_image: np.ndarray) -> list[Detection]:
        height, width = bgr_image.shape[:2]
        label = self._labels[0]
        box_width = width * 0.4
        box_height = height * 0.4
        x1 = (width - box_width) / 2.0
        y1 = (height - box_height) / 2.0
        x2 = x1 + box_width
        y2 = y1 + box_height
        return [Detection((x1, y1, x2, y2), 0, label, self._score)]


class YoloWorldDetector:
    """Adapter around the official YOLO-World MMDetection-style API."""

    def __init__(
        self,
        model_config: str,
        checkpoint_path: str,
        text_prompt: str,
        device: str = "cuda:0",
        confidence_threshold: float = 0.2,
        max_detections: int = 100,
    ) -> None:
        self._model_config = Path(model_config).expanduser()
        self._checkpoint_path = Path(checkpoint_path).expanduser()
        self._device = device
        self._confidence_threshold = confidence_threshold
        self._max_detections = max_detections
        self._labels = parse_text_prompt(text_prompt)
        self._texts = labels_to_yolo_world_texts(self._labels)

        if not self._model_config.is_file():
            raise FileNotFoundError(f"YOLO-World model_config not found: {self._model_config}")
        if not self._checkpoint_path.is_file():
            raise FileNotFoundError(f"YOLO-World checkpoint_path not found: {self._checkpoint_path}")

        try:
            import torch
            from mmengine.config import Config
            from mmengine.dataset import Compose
            from mmdet.apis import init_detector
            from mmdet.utils import get_test_pipeline_cfg
        except ImportError as exc:
            raise ImportError(
                "YOLO-World dependencies are not importable. Install the official "
                "YOLO-World repository with `python3 -m pip install -e .` in WSL2."
            ) from exc

        self._torch = torch
        cfg = Config.fromfile(str(self._model_config))
        cfg.load_from = str(self._checkpoint_path)
        self._model = init_detector(cfg, checkpoint=str(self._checkpoint_path), device=self._device)

        test_pipeline_cfg = get_test_pipeline_cfg(cfg=cfg)
        if test_pipeline_cfg:
            test_pipeline_cfg[0].type = "mmdet.LoadImageFromNDArray"
        self._test_pipeline = Compose(test_pipeline_cfg)

        if hasattr(self._model, "reparameterize"):
            self._model.reparameterize(self._texts)

    def detect(self, bgr_image: np.ndarray) -> list[Detection]:
        rgb_image = bgr_image[:, :, [2, 1, 0]]
        data_info = {"img": rgb_image, "img_id": 0, "texts": self._texts}
        data_info = self._test_pipeline(data_info)
        data_batch = {
            "inputs": data_info["inputs"].unsqueeze(0),
            "data_samples": [data_info["data_samples"]],
        }

        with self._torch.no_grad():
            output = self._model.test_step(data_batch)[0]

        pred_instances = output.pred_instances
        pred_instances = pred_instances[
            pred_instances.scores.float() > self._confidence_threshold
        ]
        if len(pred_instances.scores) > self._max_detections:
            indices = pred_instances.scores.float().topk(self._max_detections)[1]
            pred_instances = pred_instances[indices]

        pred_instances = pred_instances.cpu().numpy()
        boxes = pred_instances.bboxes
        class_ids = pred_instances.labels
        scores = pred_instances.scores

        detections: list[Detection] = []
        for box, class_id, score in zip(boxes, class_ids, scores):
            class_index = int(class_id)
            if class_index >= len(self._labels):
                continue
            detections.append(
                Detection(
                    xyxy=tuple(float(value) for value in box),
                    class_id=class_index,
                    label=self._labels[class_index],
                    score=float(score),
                )
            )
        return detections
