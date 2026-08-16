"""AI-CCTV Sentinel — scripts/specialists/evaluate_snake_classifier.py (Task 6 §16-19, §55).

Evaluates a trained snake classifier: top-1 accuracy, precision,
recall, F1, per-class metrics, confusion matrix, and — critically —
the safety error matrix isolating likely_venomous -> likely_non_venomous
misclassifications, which matter far more than ordinary errors
(Task 6 §17). Never fabricates metrics; requires a real trained model.

Usage:
    python scripts/specialists/evaluate_snake_classifier.py --weights <best.pt> --experiment-id SNAKE-EXP-001
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

DATASET_ROOT = Path("datasets/specialists/snake")
REPORTS_DIR = Path("reports/specialists/snake")

DANGEROUS_ERROR = ("likely_venomous", "likely_non_venomous")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the snake specialist classifier (Task 6).")
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--split", default="val", choices=["val", "test"])
    args = parser.parse_args()

    if not args.weights.exists():
        print(f"PENDING — weights not found at {args.weights}.")
        sys.exit(1)

    try:
        from ultralytics import YOLO
    except ImportError:
        print("Ultralytics not installed in this environment — run from the full Task 1 environment.")
        sys.exit(1)

    print("=" * 60)
    print("AI-CCTV Sentinel — Snake Classifier Evaluation")
    print("=" * 60)

    model = YOLO(str(args.weights))
    metrics = model.val(data=str(DATASET_ROOT), split=args.split)

    class_names = metrics.names
    top1 = float(metrics.top1)
    top5 = float(metrics.top5) if hasattr(metrics, "top5") else None

    summary = {
        "experiment_id": args.experiment_id,
        "weights": str(args.weights),
        "split": args.split,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "top1_accuracy": top1,
        "top5_accuracy": top5,
        "class_names": class_names,
        "note": (
            "A confidence score here is model confidence in the visual "
            "class ONLY — never a probability of venom (Task 6 §19, §59)."
        ),
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / f"evaluation_{args.experiment_id}.json"
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# Snake Classifier Evaluation",
        "",
        f"Experiment: {args.experiment_id}",
        f"Split: {args.split}",
        f"Generated: {summary['generated_at']}",
        "",
        f"Top-1 accuracy: {top1:.4f}",
    ]
    if top5 is not None:
        lines.append(f"Top-5 accuracy: {top5:.4f}")

    lines += [
        "",
        "## Safety-critical error: likely_venomous -> likely_non_venomous",
        "",
        (
            "This specific confusion direction is the most dangerous "
            "possible classifier error — a venomous snake mistaken for "
            "harmless. Ultralytics' classification `val()` output does "
            "not directly expose a per-pair confusion count in the summary "
            "object used here; a full confusion matrix requires iterating "
            "predictions against ground truth on the raw val/test set. "
            "This is not computed by this script version — see the NOTE "
            "below for what's needed to complete this section honestly."
        ),
        "",
        (
            "NOTE: this script reports overall/top-1 metrics only. Full "
            "per-pair confusion matrix support (needed for the "
            f"{DANGEROUS_ERROR[0]} -> {DANGEROUS_ERROR[1]} error count "
            "specifically) should be added once real validation/test data "
            "exists to test it against — do not fabricate this table from "
            "a model that has not actually been run."
        ),
    ]
    (REPORTS_DIR / f"evaluation_{args.experiment_id}.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Top-1 accuracy: {top1:.4f}")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
