from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

from sim2real_eval.domain_randomization import TRIAL_FIELDNAMES


RESULT_FIELDNAMES = TRIAL_FIELDNAMES + [
    "detections_count",
    "target_detected",
    "mean_confidence",
    "localized",
    "localized_x",
    "localized_y",
    "localized_z",
]


@dataclass(frozen=True)
class TrialResult:
    row: dict[str, str]

    @property
    def trial_id(self) -> int:
        return int(self.row.get("trial_id", 0))

    @property
    def target_detected(self) -> bool:
        return parse_bool(self.row.get("target_detected", "false"))

    @property
    def mean_confidence(self) -> float:
        return parse_float(self.row.get("mean_confidence", "0.0"))

    @property
    def localized(self) -> bool:
        return parse_bool(self.row.get("localized", "false"))

    @property
    def localized_point(self) -> tuple[float, float, float] | None:
        if not self.localized:
            return None
        try:
            return (
                float(self.row["localized_x"]),
                float(self.row["localized_y"]),
                float(self.row["localized_z"]),
            )
        except (KeyError, TypeError, ValueError):
            return None


@dataclass(frozen=True)
class MetricsSummary:
    total_trials: int
    target_detection_rate: float
    localization_success_rate: float
    mean_confidence: float
    localized_mean: tuple[float, float, float]
    localized_std: tuple[float, float, float]
    worst_trials: list[TrialResult]


def parse_bool(value: str | bool | int | None) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y"}


def parse_float(value: str | float | int | None) -> float:
    if value is None:
        return 0.0
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(number) or math.isinf(number):
        return 0.0
    return number


def read_results_csv(path: str | Path) -> list[TrialResult]:
    with Path(path).open("r", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        return [TrialResult(dict(row)) for row in reader]


def summarize_results(results: list[TrialResult]) -> MetricsSummary:
    total = len(results)
    if total == 0:
        return MetricsSummary(
            total_trials=0,
            target_detection_rate=0.0,
            localization_success_rate=0.0,
            mean_confidence=0.0,
            localized_mean=(0.0, 0.0, 0.0),
            localized_std=(0.0, 0.0, 0.0),
            worst_trials=[],
        )

    detected = sum(1 for result in results if result.target_detected)
    localized_points = [point for result in results if (point := result.localized_point) is not None]
    confidences = [result.mean_confidence for result in results]

    return MetricsSummary(
        total_trials=total,
        target_detection_rate=detected / total,
        localization_success_rate=len(localized_points) / total,
        mean_confidence=sum(confidences) / total,
        localized_mean=_mean_point(localized_points),
        localized_std=_std_point(localized_points),
        worst_trials=sorted(results, key=lambda result: result.mean_confidence)[: min(5, total)],
    )


def _mean_point(points: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    if not points:
        return (0.0, 0.0, 0.0)
    count = len(points)
    return (
        sum(point[0] for point in points) / count,
        sum(point[1] for point in points) / count,
        sum(point[2] for point in points) / count,
    )


def _std_point(points: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    if len(points) < 2:
        return (0.0, 0.0, 0.0)
    mean = _mean_point(points)
    count = len(points)
    return (
        math.sqrt(sum((point[0] - mean[0]) ** 2 for point in points) / count),
        math.sqrt(sum((point[1] - mean[1]) ** 2 for point in points) / count),
        math.sqrt(sum((point[2] - mean[2]) ** 2 for point in points) / count),
    )
