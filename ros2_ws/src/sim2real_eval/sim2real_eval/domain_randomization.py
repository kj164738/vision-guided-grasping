from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


TRIAL_FIELDNAMES = [
    "trial_id",
    "seed",
    "light_intensity",
    "table_color_r",
    "table_color_g",
    "table_color_b",
    "object_color_r",
    "object_color_g",
    "object_color_b",
    "camera_x",
    "camera_y",
    "camera_z",
    "camera_roll",
    "camera_pitch",
    "camera_yaw",
    "target_label",
]


@dataclass(frozen=True)
class TrialConfig:
    trial_id: int
    seed: int
    light_intensity: float
    table_color_r: float
    table_color_g: float
    table_color_b: float
    object_color_r: float
    object_color_g: float
    object_color_b: float
    camera_x: float
    camera_y: float
    camera_z: float
    camera_roll: float
    camera_pitch: float
    camera_yaw: float
    target_label: str

    def to_row(self) -> dict[str, str]:
        return {
            "trial_id": str(self.trial_id),
            "seed": str(self.seed),
            "light_intensity": f"{self.light_intensity:.6f}",
            "table_color_r": f"{self.table_color_r:.6f}",
            "table_color_g": f"{self.table_color_g:.6f}",
            "table_color_b": f"{self.table_color_b:.6f}",
            "object_color_r": f"{self.object_color_r:.6f}",
            "object_color_g": f"{self.object_color_g:.6f}",
            "object_color_b": f"{self.object_color_b:.6f}",
            "camera_x": f"{self.camera_x:.6f}",
            "camera_y": f"{self.camera_y:.6f}",
            "camera_z": f"{self.camera_z:.6f}",
            "camera_roll": f"{self.camera_roll:.6f}",
            "camera_pitch": f"{self.camera_pitch:.6f}",
            "camera_yaw": f"{self.camera_yaw:.6f}",
            "target_label": self.target_label,
        }

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "TrialConfig":
        return cls(
            trial_id=int(row["trial_id"]),
            seed=int(row["seed"]),
            light_intensity=float(row["light_intensity"]),
            table_color_r=float(row["table_color_r"]),
            table_color_g=float(row["table_color_g"]),
            table_color_b=float(row["table_color_b"]),
            object_color_r=float(row["object_color_r"]),
            object_color_g=float(row["object_color_g"]),
            object_color_b=float(row["object_color_b"]),
            camera_x=float(row["camera_x"]),
            camera_y=float(row["camera_y"]),
            camera_z=float(row["camera_z"]),
            camera_roll=float(row["camera_roll"]),
            camera_pitch=float(row["camera_pitch"]),
            camera_yaw=float(row["camera_yaw"]),
            target_label=row.get("target_label", "cube"),
        )


def generate_trials(count: int, seed: int = 0, target_label: str = "cube") -> list[TrialConfig]:
    if count < 0:
        raise ValueError("count must be non-negative")

    rng = random.Random(seed)
    trials: list[TrialConfig] = []
    for trial_id in range(count):
        trial_seed = rng.randint(0, 2**31 - 1)
        trial_rng = random.Random(trial_seed)
        trials.append(_make_trial(trial_id, trial_seed, trial_rng, target_label))
    return trials


def _make_trial(trial_id: int, seed: int, rng: random.Random, target_label: str) -> TrialConfig:
    return TrialConfig(
        trial_id=trial_id,
        seed=seed,
        light_intensity=rng.uniform(250.0, 900.0),
        table_color_r=rng.uniform(0.25, 0.75),
        table_color_g=rng.uniform(0.25, 0.75),
        table_color_b=rng.uniform(0.25, 0.75),
        object_color_r=rng.uniform(0.05, 0.95),
        object_color_g=rng.uniform(0.05, 0.95),
        object_color_b=rng.uniform(0.05, 0.95),
        camera_x=0.55 + rng.uniform(-0.05, 0.05),
        camera_y=-0.95 + rng.uniform(-0.05, 0.05),
        camera_z=0.95 + rng.uniform(-0.04, 0.04),
        camera_roll=62.0 + rng.uniform(-4.0, 4.0),
        camera_pitch=rng.uniform(-3.0, 3.0),
        camera_yaw=rng.uniform(-3.0, 3.0),
        target_label=target_label,
    )


def write_trials_csv(path: str | Path, trials: Iterable[TrialConfig]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=TRIAL_FIELDNAMES)
        writer.writeheader()
        for trial in trials:
            writer.writerow(trial.to_row())
    return output


def read_trials_csv(path: str | Path) -> list[TrialConfig]:
    with Path(path).open("r", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        return [TrialConfig.from_row(row) for row in reader]
