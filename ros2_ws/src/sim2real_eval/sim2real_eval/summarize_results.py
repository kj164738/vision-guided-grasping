from __future__ import annotations

import argparse

from sim2real_eval.metrics import read_results_csv, summarize_results
from sim2real_eval.report import render_markdown_report, write_markdown_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize Sim2Real result CSV into a Markdown report.")
    parser.add_argument("--input", default="outputs/sim2real_results.csv", help="Input result CSV path")
    parser.add_argument("--output", default="outputs/sim2real_report.md", help="Output Markdown report path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = read_results_csv(args.input)
    summary = summarize_results(results)
    report = render_markdown_report(summary, results)
    output = write_markdown_report(args.output, report)
    print(f"Wrote report for {summary.total_trials} trials to {output}")


if __name__ == "__main__":
    main()
