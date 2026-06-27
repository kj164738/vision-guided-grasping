from __future__ import annotations

from dataclasses import dataclass

from sim_control.panda_presets import PANDA_JOINT_NAMES


@dataclass(frozen=True)
class GraspPreset:
    name: str
    positions: tuple[float, ...]


GRASP_PRESETS: tuple[GraspPreset, ...] = (
    GraspPreset("approach_table", (0.35, -0.70, 0.10, -2.10, -0.10, 1.55, 0.95)),
    GraspPreset("descend_demo", (0.42, -0.48, 0.18, -2.25, -0.18, 1.78, 0.98)),
    GraspPreset("lift_demo", (0.38, -0.88, 0.12, -2.00, -0.08, 1.42, 0.92)),
    GraspPreset("retreat_demo", (0.00, -0.60, 0.00, -2.30, 0.00, 1.70, 0.80)),
)


def get_grasp_preset(name: str) -> GraspPreset:
    for preset in GRASP_PRESETS:
        if preset.name == name:
            return preset
    available = ", ".join(preset.name for preset in GRASP_PRESETS)
    raise ValueError(f"Unknown grasp preset '{name}'. Available presets: {available}")


def validate_grasp_preset(preset: GraspPreset) -> None:
    if len(preset.positions) != len(PANDA_JOINT_NAMES):
        raise ValueError(
            f"Preset '{preset.name}' has {len(preset.positions)} positions, "
            f"expected {len(PANDA_JOINT_NAMES)}"
        )
    for value in preset.positions:
        if value < -3.2 or value > 3.2:
            raise ValueError(f"Preset '{preset.name}' contains out-of-range joint value {value}")


def validate_all_grasp_presets() -> None:
    names = tuple(preset.name for preset in GRASP_PRESETS)
    if len(names) != len(set(names)):
        raise ValueError("Grasp preset names must be unique")
    for preset in GRASP_PRESETS:
        validate_grasp_preset(preset)
