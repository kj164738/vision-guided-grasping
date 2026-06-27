from sim_control.panda_presets import PANDA_JOINT_NAMES

from grasp_execution.grasp_presets import GRASP_PRESETS, validate_all_grasp_presets


def test_grasp_presets_have_valid_joint_count_and_range():
    validate_all_grasp_presets()
    assert tuple(preset.name for preset in GRASP_PRESETS) == (
        "approach_table",
        "descend_demo",
        "lift_demo",
        "retreat_demo",
    )
    for preset in GRASP_PRESETS:
        assert len(preset.positions) == len(PANDA_JOINT_NAMES)
        assert all(-3.2 <= value <= 3.2 for value in preset.positions)
