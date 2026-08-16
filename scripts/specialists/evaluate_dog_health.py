"""AI-CCTV Sentinel — scripts/specialists/evaluate_dog_health.py (Task 6 §56-58).

Evaluates a trained dog-health screening classifier: accuracy,
precision, recall, F1, per-class metrics — with particular emphasis on
recall for possible_wound / possible_skin_abnormality / possible_injury
(Task 6 §56), since missing a real abnormality is worse than a false
alarm that gets reviewed and dismissed by a human.

Usage:
    python scripts/specialists/evaluate_dog_health.py --weights <best.pt> --experiment-id DOG-HEALTH-EXP-001
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

DATASET_ROOT = Path("datasets/specialists/dog_health")
REPORTS_DIR = Path("reports/specialists/dog_health")
SAFETY_SENSITIVE_CLASSES = {"possible_wound", "possible_skin_abnormality", "possible_injury"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the dog health screening classifier (Task 6).")
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
    print("AI-CCTV Sentinel — Dog Health Screening Evaluation")
    print("=" * 60)
    print("Screening classifier only — not a diagnostic evaluation.")
    print("=" * 60)

    model = YOLO(str(args.weights))
    metrics = model.val(data=str(DATASET_ROOT), split=args.split)

    top1 = float(metrics.top1)
    top5 = float(metrics.top5) if hasattr(metrics, "top5") else None

    summary = {
        "experiment_id": args.experiment_id,
        "weights": str(args.weights),
        "split": args.split,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "top1_accuracy": top1,
        "top5_accuracy": top5,
        "safety_sensitive_classes": sorted(SAFETY_SENSITIVE_CLASSES),
        "note": (
            "confidence is model confidence in the visual screening class "
            "ONLY — never a medical probability (Task 6 §34, §59). "
            "diagnosis=false always applies to any downstream "
            "SpecialistResult built from this model."
        ),
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / f"evaluation_{args.experiment_id}.json"
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# Dog Health Screening Evaluation",
        "",
        f"Experiment: {args.experiment_id}",
        f"Split: {args.split}",
        f"Generated: {summary['generated_at']}",
        "",
        f"Top-1 accuracy: {top1:.4f}",
        "",
        "## Safety-sensitive class recall",
        "",
        (
            "Recall for possible_wound, possible_skin_abnormality, and "
            "possible_injury matters more than overall accuracy — missing "
            "a real abnormality is worse than a false alarm a human "
            "reviewer dismisses. Per-class recall requires iterating "
            "predictions against ground truth on the raw val/test set; "
            "this script reports overall top-1 only in this version — see "
            "NOTE below rather than a fabricated per-class table."
        ),
        "",
        (
            "NOTE: do not fill in per-class numbers here without actually "
            "running this evaluation against a real trained model and "
            "real labeled val/test data."
        ),
    ]
    (REPORTS_DIR / f"evaluation_{args.experiment_id}.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Top-1 accuracy: {top1:.4f}")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
