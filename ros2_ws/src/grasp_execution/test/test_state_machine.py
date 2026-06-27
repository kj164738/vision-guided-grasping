from grasp_execution.state_machine import (
    GRASP_STATES,
    GraspStateMachine,
    LocalizedTarget,
    choose_target,
)


def test_state_machine_sequence_is_fixed():
    machine = GraspStateMachine()
    observed = [machine.state]
    while not machine.done:
        observed.append(machine.advance())

    assert tuple(observed) == GRASP_STATES


def test_start_moves_from_idle_to_approach():
    machine = GraspStateMachine()

    assert machine.start() == "approach"
    assert machine.current_preset_name() == "approach_table"


def test_choose_target_without_label_returns_first_target():
    targets = [
        LocalizedTarget("cup", 0.7, 1.0, 2.0, 3.0),
        LocalizedTarget("box", 0.9, 4.0, 5.0, 6.0),
    ]

    assert choose_target(targets, "") == targets[0]


def test_choose_target_with_label_returns_matching_target():
    targets = [
        LocalizedTarget("cup", 0.7, 1.0, 2.0, 3.0),
        LocalizedTarget("box", 0.9, 4.0, 5.0, 6.0),
    ]

    assert choose_target(targets, "box") == targets[1]


def test_choose_target_returns_none_for_empty_or_missing_label():
    targets = [LocalizedTarget("cup", 0.7, 1.0, 2.0, 3.0)]

    assert choose_target([], "") is None
    assert choose_target(targets, "bottle") is None
