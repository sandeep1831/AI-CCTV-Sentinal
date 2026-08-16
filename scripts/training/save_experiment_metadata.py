"""AI-CCTV Sentinel — scripts/training/save_experiment_metadata.py (Task 5 §48-50, §82-84).

Registers a trained candidate model into models/candidates/, computing
its SHA-256 checksum and writing a metadata JSON that ties it to the
exact dataset version/hash and class mapping it was trained/evaluated
against (Task 5 §82 — prevents accidentally evaluating a model against
an incompatible dataset later). Status is always CANDIDATE here — this
script never marks a model PRODUCTION (Task 5 §50; that transition
belongs to the ModelRegistry lifecycle defined in Task 2's
ai/learning/interfaces.py, exercised by a later integration task).

Usage:
    python scripts/training/save_experiment_metadata.py \\
        --weights runs/detect/sentinel_yolo26n_baseline/weights/best.pt \\
        --experiment-id EXP-001 --model-version v1.0.0
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_baseline import dataset_hash, detect_environment  # noqa: E402

CLASSES_CONFIG = Path("configs/classes.yaml")
CANDIDATES_DIR = Path("models/candidates")


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_class_mapping() -> dict:
    import yaml

    if not CLASSES_CONFIG.exists():
        return {}
    data = yaml.safe_load(CLASSES_CONFIG.read_text(encoding="utf-8")) or {}
    return data.get("classes", {})


def main() -> None:
    parser = argparse.ArgumentParser(description="Register a trained model candidate (Task 5).")
    parser.add_argument("--weights", type=Path, required=True, help="Path to best.pt")
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--model-version", required=True, help="e.g. v1.0.0")
    parser.add_argument("--model-family", default="YOLO26n")
    args = parser.parse_args()

    if not args.weights.exists():
        print(f"PENDING — weights not found at {args.weights}. Cannot register a model that doesn't exist.")
        sys.exit(1)

    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    model_name = f"sentinel-yolo26n-{args.model_version}"
    dest_weights = CANDIDATES_DIR / f"{model_name}.pt"
    shutil.copy2(args.weights, dest_weights)

    validation_metrics_path = Path("reports/validation") / args.experiment_id / "validation_metrics.json"
    test_metrics_path = Path("reports/test") / args.experiment_id / "test_metrics.json"
    validation_metrics = (
        json.loads(validation_metrics_path.read_text(encoding="utf-8")) if validation_metrics_path.exists() else None
    )
    test_metrics = json.loads(test_metrics_path.read_text(encoding="utf-8")) if test_metrics_path.exists() else None

    environment = detect_environment()

    metadata = {
        "model_version": args.model_version,
        "model_name": model_name,
        "model_family": args.model_family,
        "model_size": "nano" if "26n" in args.model_family.lower() else "unknown",
        "dataset_version": "1.0.0",
        "dataset_hash": dataset_hash(),
        "class_mapping": load_class_mapping(),
        "training_experiment": args.experiment_id,
        "training_date": date.today().isoformat(),
        "python_version": environment.get("python_version"),
        "pytorch_version": environment.get("pytorch_version"),
        "ultralytics_version": environment.get("ultralytics_version"),
        "hardware": {
            "gpu": environment.get("gpu"),
            "cpu": environment.get("cpu"),
            "os": environment.get("os"),
        },
        "validation_metrics": validation_metrics["overall"] if validation_metrics else "PENDING",
        "test_metrics": test_metrics["overall"] if test_metrics else "PENDING",
        "model_sha256": sha256_of(dest_weights),
        "status": "CANDIDATE",  # never set to PRODUCTION here — see ai/learning/interfaces.py ModelRegistry
    }

    metadata_path = CANDIDATES_DIR / f"{model_name}.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print("=" * 60)
    print("AI-CCTV Sentinel — Model Registered")
    print("=" * 60)
    print(f"Model     : {dest_weights}")
    print(f"Metadata  : {metadata_path}")
    print(f"SHA-256   : {metadata['model_sha256']}")
    print(f"Status    : CANDIDATE")
    print("=" * 60)


if __name__ == "__main__":
    main()
