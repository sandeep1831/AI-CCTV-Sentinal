"""AI-CCTV Sentinel — scripts/specialists/train_dog_health_classifier.py (Task 6 §28, §52, §54).

Trains yolo26n-cls.pt on datasets/specialists/dog_health/
(DOG-HEALTH-EXP-001). This is the script most likely to be blocked in
practice — Task 6 §52 is explicit: "If insufficient verified
wound/abnormality images exist: DO NOT TRAIN A FAKE MODEL." This
script enforces that as a hard refusal, not a suggestion.

Usage:
    python scripts/specialists/train_dog_health_classifier.py [--min-per-class 20]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

CONFIG_PATH = Path("configs/specialists/dog_health.yaml")
DATASET_ROOT = Path("datasets/specialists/dog_health")


def count_samples() -> dict[str, int]:
    train_dir = DATASET_ROOT / "train"
    counts: dict[str, int] = {}
    if not train_dir.exists():
        return counts
    for category_dir in train_dir.iterdir():
        if category_dir.is_dir():
            images = [p for p in category_dir.glob("*") if p.is_file() and p.name != ".gitkeep"]
            counts[category_dir.name] = len(images)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the dog health screening classifier (Task 6).")
    parser.add_argument("--min-per-class", type=int, default=20)
    args = parser.parse_args()

    print("=" * 60)
    print("AI-CCTV Sentinel — Dog Health Screening Classifier Training")
    print("=" * 60)
    print("This is a VISUAL SCREENING classifier, not a diagnostic tool.")
    print("=" * 60)

    if not CONFIG_PATH.exists():
        print(f"PENDING — {CONFIG_PATH} not found.")
        sys.exit(1)
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))

    train_counts = count_samples()
    total_train = sum(train_counts.values())
    print(f"Train samples by category: {train_counts}")

    if total_train == 0:
        print()
        print(
            "DOG HEALTH SCREENING: DATA INSUFFICIENT (0 samples). "
            "Run create_dog_health_dataset.py after staging licensed, "
            "labeled data first. Per Task 6 §52, no model is trained."
        )
        sys.exit(1)

    under_threshold = {c: n for c, n in train_counts.items() if n < args.min_per_class}
    if under_threshold:
        print()
        print(
            f"DOG HEALTH SCREENING: DATA INSUFFICIENT — under {args.min_per_class}/class: "
            f"{under_threshold}. Per Task 6 §52, this is NOT trained on with "
            "fabricated or duplicated data. The project continues with dog "
            "detection + visibility assessment only until sufficient "
            "legitimate data is collected."
        )
        sys.exit(1)

    try:
        from ultralytics import YOLO
    except ImportError:
        print("Ultralytics not installed in this environment — run from the full Task 1 environment.")
        sys.exit(1)

    training_cfg = config["training"]
    model = YOLO(config["model"]["weights"])

    start = datetime.now(timezone.utc)
    results = model.train(
        data=str(DATASET_ROOT),
        epochs=training_cfg["epochs"],
        imgsz=training_cfg["image_size"],
        batch=training_cfg["batch"],
        device=training_cfg["device"],
        patience=training_cfg["patience"],
        seed=training_cfg["seed"],
        project=training_cfg["project"],
        name=training_cfg["name"],
    )
    end = datetime.now(timezone.utc)

    save_dir = Path(getattr(results, "save_dir", training_cfg["project"]))
    experiment_dir = Path("runs/specialists/dog_health") / config["experiment_id"]
    experiment_dir.mkdir(parents=True, exist_ok=True)
    (experiment_dir / "training_duration.json").write_text(
        json.dumps(
            {
                "training_start": start.isoformat(),
                "training_end": end.isoformat(),
                "training_duration_seconds": (end - start).total_seconds(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print("=" * 60)
    print(f"Training complete. Run directory: {save_dir}")
    print(f"best.pt: {save_dir / 'weights' / 'best.pt'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
