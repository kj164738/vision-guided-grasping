import pytest

from sim_control.panda_presets import PANDA_JOINT_NAMES, PRESETS, get_preset, preset_names, validate_all_presets


def test_panda_joint_names_match_expected_command_interface():
    assert PANDA_JOINT_NAMES == tuple(f"panda_joint{index}" for index in range(1, 8))


def test_required_presets_are_defined():
    assert preset_names() == ("home", "observe_table", "pre_grasp_demo")


def test_presets_have_seven_reasonable_radian_values():
    validate_all_presets()
    for preset in PRESETS:
        assert len(preset.positions) == len(PANDA_JOINT_NAMES)
        assert all(-3.2 <= value <= 3.2 for value in preset.positions)


def test_get_preset_rejects_unknown_name():
    with pytest.raises(ValueError, match="Unknown Panda joint preset"):
        get_preset("not_a_preset")
