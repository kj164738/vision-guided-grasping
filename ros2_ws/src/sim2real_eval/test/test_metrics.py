from sim2real_eval.metrics import TrialResult, summarize_results


def test_metrics_handle_empty_results():
    summary = summarize_results([])

    assert summary.total_trials == 0
    assert summary.target_detection_rate == 0.0
    assert summary.localization_success_rate == 0.0
    assert summary.mean_confidence == 0.0
    assert summary.localized_mean == (0.0, 0.0, 0.0)


def test_metrics_handle_missing_targets():
    results = [
        TrialResult({"trial_id": "0", "target_detected": "false", "mean_confidence": "0.0", "localized": "false"}),
        TrialResult({"trial_id": "1", "target_detected": "false", "mean_confidence": "0.1", "localized": "false"}),
    ]

    summary = summarize_results(results)

    assert summary.total_trials == 2
    assert summary.target_detection_rate == 0.0
    assert summary.localization_success_rate == 0.0
    assert summary.mean_confidence == 0.05


def test_metrics_compute_successful_localized_points():
    results = [
        TrialResult(
            {
                "trial_id": "0",
                "target_detected": "true",
                "mean_confidence": "0.8",
                "localized": "true",
                "localized_x": "0.5",
                "localized_y": "0.1",
                "localized_z": "0.4",
            }
        ),
        TrialResult(
            {
                "trial_id": "1",
                "target_detected": "true",
                "mean_confidence": "0.6",
                "localized": "true",
                "localized_x": "0.7",
                "localized_y": "0.1",
                "localized_z": "0.6",
            }
        ),
    ]

    summary = summarize_results(results)

    assert summary.target_detection_rate == 1.0
    assert summary.localization_success_rate == 1.0
    assert summary.mean_confidence == 0.7
    assert summary.localized_mean == (0.6, 0.1, 0.5)
    assert summary.localized_std == (0.09999999999999998, 0.0, 0.09999999999999998)
    assert [result.trial_id for result in summary.worst_trials] == [1, 0]
