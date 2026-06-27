from sim2real_eval.metrics import TrialResult, summarize_results
from sim2real_eval.report import render_markdown_report


def test_markdown_report_contains_summary_and_worst_trials():
    results = [
        TrialResult(
            {
                "trial_id": "3",
                "target_label": "cube",
                "target_detected": "true",
                "localized": "true",
                "mean_confidence": "0.33",
                "localized_x": "0.5",
                "localized_y": "0.0",
                "localized_z": "0.4",
            }
        )
    ]
    summary = summarize_results(results)

    report = render_markdown_report(summary, results)

    assert "Total trials: 1" in report
    assert "Target detection rate: 100.0%" in report
    assert "Localization success rate: 100.0%" in report
    assert "Worst-Confidence Trials" in report
    assert "| 3 | cube | true | true | 0.330 |" in report
