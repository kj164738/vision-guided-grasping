from __future__ import annotations

from dataclasses import dataclass


GRASP_STATES: tuple[str, ...] = (
    "idle",
    "approach",
    "descend",
    "close_gripper",
    "lift",
    "retreat",
    "done",
)

COMMAND_STATES: tuple[str, ...] = ("approach", "descend", "lift", "retreat")

STATE_TO_PRESET: dict[str, str] = {
    "approach": "approach_table",
    "descend": "descend_demo",
    "lift": "lift_demo",
    "retreat": "retreat_demo",
}


@dataclass(frozen=True)
class LocalizedTarget:
    label: str
    score: float
    x: float
    y: float
    z: float


def choose_target(targets: list[LocalizedTarget], target_label: str = "") -> LocalizedTarget | None:
    if not targets:
        return None
    if not target_label:
        return targets[0]
    for target in targets:
        if target.label == target_label:
            return target
    return None


class GraspStateMachine:
    def __init__(self) -> None:
        self._index = 0

    @property
    def state(self) -> str:
        return GRASP_STATES[self._index]

    @property
    def done(self) -> bool:
        return self.state == "done"

    def reset(self) -> None:
        self._index = 0

    def start(self) -> str:
        if self.state == "idle":
            self._index = 1
        return self.state

    def advance(self) -> str:
        if self._index < len(GRASP_STATES) - 1:
            self._index += 1
        return self.state

    def current_preset_name(self) -> str | None:
        return STATE_TO_PRESET.get(self.state)
