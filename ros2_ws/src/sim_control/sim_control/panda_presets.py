from __future__ import annotations

from dataclasses import dataclass


PANDA_JOINT_NAMES: tuple[str, ...] = (
    "panda_joint1",
    "panda_joint2",
    "panda_joint3",
    "panda_joint4",
    "panda_joint5",
    "panda_joint6",
    "panda_joint7",
)


@dataclass(frozen=True)
class JointPreset:
    name: str
    positions: tuple[float, ...]


PRESETS: tuple[JointPreset, ...] = (
    JointPreset("home", (0.0, -0.6, 0.0, -2.3, 0.0, 1.7, 0.8)),
    JointPreset("observe_table", (0.25, -0.75, 0.0, -2.15, 0.0, 1.45, 1.05)),
    JointPreset("pre_grasp_demo", (0.45, -0.35, 0.2, -1.95, -0.2, 1.65, 0.95)),
)


def get_preset(name: str) -> JointPreset:
    for preset in PRESETS:
        if preset.name == name:
            return preset
    available = ", ".join(preset.name for preset in PRESETS)
    raise ValueError(f"Unknown Panda joint preset '{name}'. Available presets: {available}")


def preset_names() -> tuple[str, ...]:
    return tuple(preset.name for preset in PRESETS)


def validate_preset(preset: JointPreset) -> None:
    if len(preset.positions) != len(PANDA_JOINT_NAMES):
        raise ValueError(
            f"Preset '{preset.name}' has {len(preset.positions)} positions, "
            f"expected {len(PANDA_JOINT_NAMES)}"
        )
    for value in preset.positions:
        if value < -3.2 or value > 3.2:
            raise ValueError(f"Preset '{preset.name}' contains out-of-range joint value {value}")


def validate_all_presets() -> None:
    names = preset_names()
    if len(names) != len(set(names)):
        raise ValueError("Panda joint preset names must be unique")
    for preset in PRESETS:
        validate_preset(preset)
