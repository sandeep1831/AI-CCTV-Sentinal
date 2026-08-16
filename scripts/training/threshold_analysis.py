"""AI-CCTV Sentinel — scripts/training/threshold_analysis.py (Task 5 §31-33, §63).

Sweeps a range of confidence thresholds against the VALIDATION split
(never test — Task 5 §34/§43) and records precision/recall/F1/false
positives/negatives at each, so an operating threshold can be chosen
deliberately rather than assumed at 0.50. Also bins detections by
confidence range for the confidence-distribution analysis (Task 5 §31).

Usage:
    python scripts/training/threshold_analysis.py --weights <best.pt> --experiment-id EXP-001
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

DATA_YAML = Path("datasets/yolo/sentinel_v1/data.yaml")
REPORTS_ROOT = Path("reports")

DEFAULT_THRESHOLDS = [0.25, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80]


def main() -> None:
    parser = argparse.ArgumentParser(description="Confidence threshold sweep (Task 5).")
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--data", type=Path, default=DATA_YAML)
    parser.add_argument("--thresholds", type=float, nargs="+", default=DEFAULT_THRESHOLDS)
    args = parser.parse_args()

    if not args.weights.exists():
        print(f"PENDING — weights not found at {args.weights}.")
        return

    try:
        from ultralytics import YOLO
    except ImportError:
        print("Ultralytics not installed in this environment — run from the full Task 1 environment.")
        return

    print("=" * 60)
    print("AI-CCTV Sentinel — Confidence Threshold Analysis (val split)")
    print("=" * 60)

    model = YOLO(str(args.weights))
    rows = []
    for threshold in args.thresholds:
        metrics = model.val(data=str(args.data), split="val", conf=threshold, verbose=False)
        precision = float(metrics.box.mp)
        recall = float(metrics.box.mr)
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        row = {
            "threshold": threshold,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "map50": float(metrics.box.map50),
            "map50_95": float(metrics.box.map),
        }
        rows.append(row)
        print(f"Threshold {threshold:.2f} | P={precision:.4f} R={recall:.4f} F1={f1:.4f} mAP50={row['map50']:.4f}")

    best_f1_row = max(rows, key=lambda r: r["f1"]) if rows else None

    summary = {
        "experiment_id": args.experiment_id,
        "weights": str(args.weights),
        "split": "val",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sweep": rows,
        "highest_f1_threshold": best_f1_row["threshold"] if best_f1_row else None,
        "note": (
            "The highest-F1 threshold is reported for reference only. Per "
            "Task 5 §33, the final operating threshold is a project "
            "decision balancing recall (missed hazards) against false "
            "alarms — it is NOT automatically the highest-F1 value."
        ),
    }

    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_ROOT / "threshold_analysis.md"
    lines = [
        "# Threshold Analysis",
        "",
        f"Experiment: {args.experiment_id}",
        f"Generated: {summary['generated_at']}",
        "",
        "| Threshold | Precision | Recall | F1 | mAP50 | mAP50-95 |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['threshold']:.2f} | {row['precision']:.4f} | {row['recall']:.4f} "
            f"| {row['f1']:.4f} | {row['map50']:.4f} | {row['map50_95']:.4f} |"
        )
    lines.append("")
    lines.append(
        f"Highest-F1 threshold (reference only, not automatically the chosen "
        f"operating point): **{summary['highest_f1_threshold']}**"
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")

    (REPORTS_ROOT / f"threshold_analysis_{args.experiment_id}.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
