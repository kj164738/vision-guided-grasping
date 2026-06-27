from __future__ import annotations

import argparse

from sim2real_eval.domain_randomization import generate_trials, write_trials_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate deterministic Sim2Real randomization trials.")
    parser.add_argument("--count", type=int, default=10, help="Number of trial rows to generate")
    parser.add_argument("--seed", type=int, default=0, help="Global random seed")
    parser.add_argument("--target-label", default="cube", help="Expected semantic target label")
    parser.add_argument("--output", default="outputs/sim2real_trials.csv", help="Output trial CSV path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    trials = generate_trials(args.count, args.seed, args.target_label)
    output = write_trials_csv(args.output, trials)
    print(f"Wrote {len(trials)} trials to {output}")


if __name__ == "__main__":
    main()
