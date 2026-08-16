"""AI-CCTV Sentinel — scripts/training/validate_model.py (Task 5 §19-26, §78).

Loads a trained checkpoint and the dataset YAML, runs Ultralytics
validation on the VALIDATION split, and saves the real metrics it
returns (precision, recall, F1, mAP50, mAP50-95, mAP75, per-class
breakdown). Never invents a number — if the model or dataset isn't
ready, this script fails loudly rather than writing placeholder
metrics.

Usage:
    python scripts/training/validate_model.py --weights runs/detect/sentinel_yolo26n_baseline/weights/best.pt --experiment-id EXP-001
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

DATA_YAML = Path("datasets/yolo/sentinel_v1/data.yaml")
REPORTS_ROOT = Path("reports/validation")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a trained model on the val split (Task 5).")
    parser.add_argument("--weights", type=Path, required=True, help="Path to best.pt")
    parser.add_argument("--experiment-id", required=True, help="e.g. EXP-001")
    parser.add_argument("--data", type=Path, default=DATA_YAML)
    args = parser.parse_args()

    if not args.weights.exists():
        print(f"PENDING — weights not found at {args.weights}. Run train_baseline.py first.")
        sys.exit(1)
    if not args.data.exists():
        print(f"PENDING — dataset YAML not found at {args.data}.")
        sys.exit(1)

    try:
        from ultralytics import YOLO
    except ImportError:
        print("Ultralytics not installed in this environment — run from the full Task 1 environment.")
        sys.exit(1)

    output_dir = REPORTS_ROOT / args.experiment_id
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("AI-CCTV Sentinel — Model Validation")
    print("=" * 60)
    print(f"Weights : {args.weights}")
    print(f"Dataset : {args.data}")

    model = YOLO(str(args.weights))
    metrics = model.val(data=str(args.data), split="val")

    class_names = metrics.names  # {id: name}
    per_class = {}
    try:
        for idx, name in class_names.items():
            per_class[name] = {
                "precision": float(metrics.box.p[idx]) if idx < len(metrics.box.p) else None,
                "recall": float(metrics.box.r[idx]) if idx < len(metrics.box.r) else None,
                "map50": float(metrics.box.ap50[idx]) if idx < len(metrics.box.ap50) else None,
                "map50_95": float(metrics.box.ap[idx]) if idx < len(metrics.box.ap) else None,
            }
    except Exception as exc:  # noqa: BLE001
        print(f"NOTE: could not extract full per-class breakdown ({exc}); overall metrics still saved.")

    summary = {
        "experiment_id": args.experiment_id,
        "weights": str(args.weights),
        "dataset": str(args.data),
        "split": "val",
        "generated_at": datetime.now(timezone.utc).isoformat(),
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

    output_path = output_dir / "validation_metrics.json"
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("=" * 60)
    print(f"Precision   : {summary['overall']['precision']:.4f}")
    print(f"Recall      : {summary['overall']['recall']:.4f}")
    print(f"F1          : {summary['overall']['f1']:.4f}")
    print(f"mAP50       : {summary['overall']['map50']:.4f}")
    print(f"mAP50-95    : {summary['overall']['map50_95']:.4f}")
    print("=" * 60)
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
