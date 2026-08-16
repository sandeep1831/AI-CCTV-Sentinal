"""AI-CCTV Sentinel — scripts/training/train_baseline.py (Task 5 §8-18, §77).

Main training entry point. Responsibilities only — no evaluation/report
logic lives here (that's validate_model.py / evaluate_test.py):

    1. Load configuration (configs/training/baseline.yaml)
    2. Validate dataset (via preflight_check.py's gate — refuses to run if not READY)
    3. Detect hardware
    4. Load YOLO26n pretrained weights
    5. Train
    6. Save experiment metadata (environment.json)
    7. Report final checkpoint/results paths

This script REFUSES to start if scripts/training/preflight_check.py
would report NOT READY (Task 5 §5). It does not fabricate a dataset,
does not lower the bar, and does not train on a subset that hasn't
passed Task 4 validation.

Usage:
    python scripts/training/train_baseline.py [--config configs/training/baseline.yaml]
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from preflight_check import (  # noqa: E402
    check_class_mapping,
    check_dataset_yaml,
    check_images_readable,
    check_split_dir,
)

DEFAULT_CONFIG = Path("configs/training/baseline.yaml")
EXPERIMENTS_ROOT = Path("runs/experiments")


def run_preflight() -> bool:
    checks = [
        check_dataset_yaml(),
        check_split_dir("train")[:2],
        check_class_mapping(),
        check_images_readable(),
    ]
    return all(passed for passed, _ in checks)


def detect_environment() -> dict:
    env: dict = {
        "python_version": platform.python_version(),
        "os": platform.platform(),
        "cpu": platform.processor() or "unknown",
    }
    try:
        import torch

        env["pytorch_version"] = torch.__version__
        env["cuda_available"] = torch.cuda.is_available()
        env["cuda_version"] = torch.version.cuda if torch.cuda.is_available() else None
        env["gpu"] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    except ImportError:
        env["pytorch_version"] = None
        env["cuda_available"] = False
        env["cuda_version"] = None
        env["gpu"] = None

    try:
        import ultralytics

        env["ultralytics_version"] = ultralytics.__version__
    except ImportError:
        env["ultralytics_version"] = None

    try:
        env["git_commit"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:  # noqa: BLE001
        env["git_commit"] = None

    return env


def dataset_hash() -> str | None:
    """SHA-256 of the generated data.yaml, as a lightweight dataset
    fingerprint. Task 4's dataset_statistics.json is the authoritative
    sample-level record; this is just enough to detect "which data.yaml
    produced this run" (Task 5 §14, §84)."""

    import hashlib

    data_yaml = Path("datasets/yolo/sentinel_v1/data.yaml")
    if not data_yaml.exists():
        return None
    return hashlib.sha256(data_yaml.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the YOLO26n baseline (Task 5).")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()

    print("=" * 60)
    print("AI-CCTV Sentinel — Baseline Training")
    print("=" * 60)

    if not run_preflight():
        print(
            "PREFLIGHT FAILED — refusing to start training. Run "
            "'python scripts/training/preflight_check.py' for the full "
            "report. Per Task 5 §5, training does not start until the "
            "Task 4 dataset is actually valid and populated."
        )
        sys.exit(1)

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    experiment_id = config["experiment"]["id"]
    experiment_dir = EXPERIMENTS_ROOT / experiment_id
    experiment_dir.mkdir(parents=True, exist_ok=True)

    environment = detect_environment()
    environment.update(
        {
            "experiment_id": experiment_id,
            "config_file": str(args.config),
            "dataset_path": config["dataset"]["path"],
            "dataset_version": config["dataset"]["version"],
            "dataset_hash": dataset_hash(),
            "seed": config["training"]["seed"],
            "image_size": config["training"]["image_size"],
            "batch": config["training"]["batch"],
            "epochs": config["training"]["epochs"],
            "patience": config["training"]["patience"],
            "device_requested": config["training"]["device"],
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    (experiment_dir / "environment.json").write_text(json.dumps(environment, indent=2), encoding="utf-8")
    print(f"Environment recorded: {experiment_dir / 'environment.json'}")

    if environment["ultralytics_version"] is None or environment["pytorch_version"] is None:
        print(
            "Ultralytics/PyTorch are not installed in this environment. "
            "Training cannot proceed here — run this script from the full "
            "Task 1 environment (see README.md)."
        )
        sys.exit(1)

    from ultralytics import YOLO

    training_cfg = config["training"]
    print(f"Loading pretrained weights: {config['model']['weights']}")
    model = YOLO(config["model"]["weights"])

    training_start = datetime.now(timezone.utc)
    results = model.train(
        data=config["dataset"]["path"],
        epochs=training_cfg["epochs"],
        imgsz=training_cfg["image_size"],
        batch=training_cfg["batch"],
        device=training_cfg["device"],
        patience=training_cfg["patience"],
        workers=training_cfg["workers"],
        seed=training_cfg["seed"],
        project=training_cfg["project"],
        name=training_cfg["name"],
    )
    training_end = datetime.now(timezone.utc)

    duration_summary = {
        "training_start": training_start.isoformat(),
        "training_end": training_end.isoformat(),
        "training_duration_seconds": (training_end - training_start).total_seconds(),
    }
    (experiment_dir / "training_duration.json").write_text(
        json.dumps(duration_summary, indent=2), encoding="utf-8"
    )

    save_dir = Path(getattr(results, "save_dir", training_cfg["project"]))
    print("=" * 60)
    print("Training complete.")
    print(f"Run directory : {save_dir}")
    print(f"best.pt       : {save_dir / 'weights' / 'best.pt'}")
    print(f"last.pt       : {save_dir / 'weights' / 'last.pt'}")
    print(f"results.csv   : {save_dir / 'results.csv'}")
    print("=" * 60)
    print(
        "NEXT: run scripts/training/validate_model.py, then "
        "scripts/training/threshold_analysis.py, then (only once the "
        "protocol is frozen) scripts/training/evaluate_test.py."
    )


if __name__ == "__main__":
    main()
