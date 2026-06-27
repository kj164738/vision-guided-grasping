from __future__ import annotations

from pathlib import Path

from sim2real_eval.metrics import MetricsSummary, TrialResult


def render_markdown_report(
    summary: MetricsSummary,
    results: list[TrialResult],
    title: str = "Stage 5 Sim2Real Evaluation Report",
) -> str:
    lines = [
        f"# {title}",
        "",
        "## Summary Metrics",
        "",
        f"- Total trials: {summary.total_trials}",
        f"- Target detection rate: {_format_percent(summary.target_detection_rate)}",
        f"- Localization success rate: {_format_percent(summary.localization_success_rate)}",
        f"- Mean confidence: {summary.mean_confidence:.3f}",
        (
            "- Localized point mean (x, y, z): "
            f"({summary.localized_mean[0]:.3f}, {summary.localized_mean[1]:.3f}, {summary.localized_mean[2]:.3f}) m"
        ),
        (
            "- Localized point std (x, y, z): "
            f"({summary.localized_std[0]:.3f}, {summary.localized_std[1]:.3f}, {summary.localized_std[2]:.3f}) m"
        ),
        "",
        "## Worst-Confidence Trials",
        "",
    ]

    lines.extend(_render_worst_trials_table(summary.worst_trials))
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "This report summarizes randomized simulation trials only. It is intended to expose detection and",
            "localization sensitivity before a full real-robot or real-domain evaluation is available.",
            "",
        ]
    )
    if results and not summary.worst_trials:
        lines.append("No worst-confidence rows were available.")
    return "\n".join(lines)


def write_markdown_report(path: str | Path, content: str) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    return output


def _format_percent(value: float) -> str:
    return f"{value * 100.0:.1f}%"


def _render_worst_trials_table(worst_trials: list[TrialResult]) -> list[str]:
    if not worst_trials:
        return ["No trial rows were provided."]

    lines = [
        "| trial_id | target_label | target_detected | localized | mean_confidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for result in worst_trials:
        row = result.row
        lines.append(
            "| "
            f"{row.get('trial_id', '')} | "
            f"{row.get('target_label', '')} | "
            f"{row.get('target_detected', '')} | "
            f"{row.get('localized', '')} | "
            f"{result.mean_confidence:.3f} |"
        )
    return lines
