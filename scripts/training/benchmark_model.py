"""AI-CCTV Sentinel — scripts/training/benchmark_model.py (Task 5 §40-42, §73).

For Task 5, basic PyTorch inference-speed measurement on actual
development hardware is sufficient (§73) — this script does NOT
perform a full edge-deployment benchmark or export to ONNX/TensorRT
yet (that's Task 21). It measures real latency/FPS on whatever
hardware it's actually run on, and records what resource usage can be
reliably queried (GPU/CPU/RAM) — never invented (§42).

Usage:
    python scripts/training/benchmark_model.py --weights <best.pt> --experiment-id EXP-001 [--runs 50]
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

REPORTS_ROOT = Path("reports")


def get_resource_snapshot() -> dict:
    snapshot: dict = {}
    try:
        import torch

        if torch.cuda.is_available():
            snapshot["gpu_name"] = torch.cuda.get_device_name(0)
            snapshot["gpu_memory_allocated_mb"] = torch.cuda.memory_allocated(0) / 1024**2
            snapshot["gpu_memory_reserved_mb"] = torch.cuda.memory_reserved(0) / 1024**2
        else:
            snapshot["gpu_name"] = None
    except ImportError:
        snapshot["gpu_name"] = None

    try:
        import psutil

        snapshot["cpu_percent"] = psutil.cpu_percent(interval=0.1)
        snapshot["ram_used_gb"] = psutil.virtual_memory().used / 1024**3
    except ImportError:
        snapshot["cpu_percent"] = None
        snapshot["ram_used_gb"] = None
        snapshot["note"] = "psutil not installed — CPU/RAM figures unavailable, not invented"

    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description="Basic PyTorch inference benchmark (Task 5).")
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--image-size", type=int, default=640)
    parser.add_argument("--runs", type=int, default=50, help="Number of timed inference passes")
    parser.add_argument("--warmup", type=int, default=5)
    args = parser.parse_args()

    if not args.weights.exists():
        print(f"PENDING — weights not found at {args.weights}.")
        return

    try:
        import numpy as np
        from ultralytics import YOLO
    except ImportError:
        print("Ultralytics/NumPy not installed in this environment — run from the full Task 1 environment.")
        return

    print("=" * 60)
    print("AI-CCTV Sentinel — Model Benchmark (PyTorch only)")
    print("=" * 60)
    print("Note: ONNX/TensorRT benchmarking is Task 21 scope, not Task 5.")

    model = YOLO(str(args.weights))
    dummy_image = np.zeros((args.image_size, args.image_size, 3), dtype=np.uint8)

    for _ in range(args.warmup):
        model.predict(source=dummy_image, verbose=False)

    latencies_ms = []
    for _ in range(args.runs):
        start = time.perf_counter()
        model.predict(source=dummy_image, verbose=False)
        latencies_ms.append((time.perf_counter() - start) * 1000)

    avg_latency = sum(latencies_ms) / len(latencies_ms)
    fps = 1000 / avg_latency

    resource_snapshot = get_resource_snapshot()

    summary = {
        "experiment_id": args.experiment_id,
        "weights": str(args.weights),
        "image_size": args.image_size,
        "runs": args.runs,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "avg_latency_ms": avg_latency,
        "min_latency_ms": min(latencies_ms),
        "max_latency_ms": max(latencies_ms),
        "fps": fps,
        "resource_snapshot": resource_snapshot,
        "note": (
            "Measured on the actual machine this script ran on — not "
            "Ultralytics' published COCO benchmark hardware, and not "
            "comparable to it (Task 5 §40)."
        ),
    }

    output_dir = REPORTS_ROOT / "benchmarks"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{args.experiment_id}_benchmark.json"
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Avg latency : {avg_latency:.2f} ms")
    print(f"FPS         : {fps:.2f}")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
