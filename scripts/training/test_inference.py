"""AI-CCTV Sentinel — scripts/training/test_inference.py (Task 5 §74).

Runs exploratory inference on a SMALL sample of images (not the
protected test split — Task 5 §74 explicitly warns against repeatedly
running inference on the test set for threshold tuning). Records
predictions, confidence, and per-image latency. Intended for sanity
checks and the error gallery, not for final metrics (those come from
evaluate_test.py).

Usage:
    python scripts/training/test_inference.py --weights <best.pt> --source path/to/sample_images/ --experiment-id EXP-001
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

REPORTS_ROOT = Path("reports")


def main() -> None:
    parser = argparse.ArgumentParser(description="Exploratory inference sample (Task 5).")
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True, help="Directory of sample images (NOT the test split)")
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--confidence", type=float, default=0.50)
    args = parser.parse_args()

    if not args.weights.exists():
        print(f"PENDING — weights not found at {args.weights}.")
        return
    if not args.source.exists():
        print(f"PENDING — source directory not found at {args.source}.")
        return

    try:
        from ultralytics import YOLO
    except ImportError:
        print("Ultralytics not installed in this environment — run from the full Task 1 environment.")
        return

    print("=" * 60)
    print("AI-CCTV Sentinel — Exploratory Inference")
    print("=" * 60)
    print(f"Source: {args.source} (sample only — NOT the protected test split)")

    model = YOLO(str(args.weights))

    output_dir = REPORTS_ROOT / "inference_samples" / args.experiment_id
    output_dir.mkdir(parents=True, exist_ok=True)

    records = []
    image_paths = sorted(
        p for p in args.source.glob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )

    for path in image_paths:
        start = time.perf_counter()
        results = model.predict(source=str(path), conf=args.confidence, save=True, project=str(output_dir), name="predictions", exist_ok=True, verbose=False)
        latency_ms = (time.perf_counter() - start) * 1000

        detections = []
        for result in results:
            for box in result.boxes:
                detections.append(
                    {
                        "class_id": int(box.cls[0]),
                        "class_name": result.names[int(box.cls[0])],
                        "confidence": float(box.conf[0]),
                    }
                )

        records.append({"image": str(path), "latency_ms": latency_ms, "detections": detections})

    avg_latency = sum(r["latency_ms"] for r in records) / len(records) if records else None
    fps = 1000 / avg_latency if avg_latency else None

    summary = {
        "experiment_id": args.experiment_id,
        "weights": str(args.weights),
        "source": str(args.source),
        "confidence_threshold": args.confidence,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "image_count": len(records),
        "avg_latency_ms": avg_latency,
        "fps": fps,
        "records": records,
    }

    output_path = output_dir / "inference_report.json"
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Images processed : {len(records)}")
    print(f"Avg latency (ms) : {avg_latency}")
    print(f"FPS              : {fps}")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
