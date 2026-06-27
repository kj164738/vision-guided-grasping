from sim2real_eval.domain_randomization import generate_trials


def test_trial_generation_is_deterministic_for_fixed_seed():
    first = generate_trials(count=5, seed=42, target_label="cube")
    second = generate_trials(count=5, seed=42, target_label="cube")

    assert first == second


def test_generated_trials_stay_within_configured_ranges():
    trials = generate_trials(count=20, seed=7, target_label="cube")

    for trial in trials:
        assert 250.0 <= trial.light_intensity <= 900.0
        assert 0.25 <= trial.table_color_r <= 0.75
        assert 0.25 <= trial.table_color_g <= 0.75
        assert 0.25 <= trial.table_color_b <= 0.75
        assert 0.05 <= trial.object_color_r <= 0.95
        assert 0.05 <= trial.object_color_g <= 0.95
        assert 0.05 <= trial.object_color_b <= 0.95
        assert 0.50 <= trial.camera_x <= 0.60
        assert -1.00 <= trial.camera_y <= -0.90
        assert 0.91 <= trial.camera_z <= 0.99
        assert 58.0 <= trial.camera_roll <= 66.0
        assert -3.0 <= trial.camera_pitch <= 3.0
        assert -3.0 <= trial.camera_yaw <= 3.0
        assert trial.target_label == "cube"
