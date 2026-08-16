"""AI-CCTV Sentinel — scripts/training/evaluate_test.py (Task 5 §43-44, §79).

Runs the FINAL evaluation on the held-out TEST split. This must only
be run once — after model selection and threshold tuning are already
decided using train/val data. Running this repeatedly to "peek" at
test performance and adjust the model defeats the purpose of a held
out test set (Task 5 §34, §43, §96).

To enforce this, the script refuses to run if
reports/test/<experiment_id>/test_metrics.json already exists, unless
--force is passed with an explicit --reason.

Usage:
    python scripts/training/evaluate_test.py --weights <best.pt> --experiment-id EXP-001
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

DATA_YAML = Path("datasets/yolo/sentinel_v1/data.yaml")
REPORTS_ROOT = Path("reports/test")


def main() -> None:
    parser = argparse.ArgumentParser(description="Final protected test-set evaluation (Task 5).")
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--data", type=Path, default=DATA_YAML)
    parser.add_argument("--force", action="store_true", help="Allow re-running an already-evaluated test.")
    parser.add_argument("--reason", default=None, help="Required with --force — why re-run the test set?")
    args = parser.parse_args()

    output_dir = REPORTS_ROOT / args.experiment_id
    output_path = output_dir / "test_metrics.json"

    if output_path.exists() and not args.force:
        print(
            f"REFUSING TO RUN: {output_path} already exists. The test set "
            "is protected and must not be evaluated repeatedly for tuning "
            "(Task 5 §34, §43). If you have a genuine reason to re-run "
            "(e.g. re-evaluating the exact same frozen model after a bug "
            "fix in this script), pass --force --reason \"...\"."
        )
        sys.exit(1)
    if args.force and not args.reason:
        print("--force requires --reason explaining why the protected test set is being re-evaluated.")
        sys.exit(1)

    if not args.weights.exists():
        print(f"PENDING — weights not found at {args.weights}.")
        sys.exit(1)

    try:
        from ultralytics import YOLO
    except ImportError:
        print("Ultralytics not installed in this environment — run from the full Task 1 environment.")
        sys.exit(1)

    print("=" * 60)
    print("AI-CCTV Sentinel — FINAL TEST SET EVALUATION")
    print("=" * 60)
    print("This is the protected, held-out test set. This run is being")
    print("recorded as the frozen, final baseline result for this model.")
    print("=" * 60)

    model = YOLO(str(args.weights))
    metrics = model.val(data=str(args.data), split="test")

    class_names = metrics.names
    per_class = {}
    for idx, name in class_names.items():
        try:
            per_class[name] = {
                "precision": float(metrics.box.p[idx]),
                "recall": float(metrics.box.r[idx]),
                "map50": float(metrics.box.ap50[idx]),
                "map50_95": float(metrics.box.ap[idx]),
            }
        except IndexError:
            per_class[name] = {"precision": None, "recall": None, "map50": None, "map50_95": None}

    summary = {
        "experiment_id": args.experiment_id,
        "weights": str(args.weights),
        "dataset": str(args.data),
        "split": "test",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "re_run": args.force,
        "re_run_reason": args.reason,
        "overall": {
            "precision": float(metrics.box.mp),
            "recall": float(metrics.box.mr),
            "map50": float(metrics.box.map50),
            "map50_95": float(metrics.box.map),
            "map75": float(metrics.box.map75) if hasattr(metrics.box, "map75") else None,
            "f1": (
                2 * metrics.box.mp * metrics.box.mr / (metrics.box.mp + metrics.box.mr)
                if (metrics.box.mp + metrics.box.mr) > 0
                else 0.0
            ),
        },
        "per_class": per_class,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Precision   : {summary['overall']['precision']:.4f}")
    print(f"Recall      : {summary['overall']['recall']:.4f}")
    print(f"F1          : {summary['overall']['f1']:.4f}")
    print(f"mAP50       : {summary['overall']['map50']:.4f}")
    print(f"mAP50-95    : {summary['overall']['map50_95']:.4f}")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
