"""AI-CCTV Sentinel — scripts/training/compare_experiments.py (Task 5 §80).

Reads real validation_metrics.json files from reports/validation/<id>/
for each requested experiment and prints/saves a comparison table.
Never fabricates a row for an experiment that hasn't actually been
validated — missing experiments are reported as PENDING, not filled
with placeholder numbers.

Usage:
    python scripts/training/compare_experiments.py EXP-001 EXP-002
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

VALIDATION_ROOT = Path("reports/validation")


def load_experiment_metrics(experiment_id: str) -> dict | None:
    path = VALIDATION_ROOT / experiment_id / "validation_metrics.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare validation metrics across experiments (Task 5).")
    parser.add_argument("experiment_ids", nargs="+", help="e.g. EXP-001 EXP-002")
    args = parser.parse_args()

    print("=" * 70)
    print("AI-CCTV Sentinel — Experiment Comparison")
    print("=" * 70)
    header = f"{'Experiment':<12}{'mAP50-95':<12}{'mAP50':<10}{'Precision':<12}{'Recall':<10}{'F1':<8}"
    print(header)
    print("-" * 70)

    rows = []
    for experiment_id in args.experiment_ids:
        data = load_experiment_metrics(experiment_id)
        if data is None:
            print(f"{experiment_id:<12}{'PENDING — not yet validated':<50}")
            continue
        overall = data["overall"]
        print(
            f"{experiment_id:<12}{overall['map50_95']:<12.4f}{overall['map50']:<10.4f}"
            f"{overall['precision']:<12.4f}{overall['recall']:<10.4f}{overall['f1']:<8.4f}"
        )
        rows.append({"experiment_id": experiment_id, **overall})

    print("=" * 70)
    if not rows:
        print(
            "No experiments have real validation metrics yet. This is "
            "expected until scripts/training/train_baseline.py and "
            "validate_model.py have actually been run against a "
            "populated dataset."
        )


if __name__ == "__main__":
    main()
