"""AI-CCTV Sentinel — scripts/specialists/train_snake_classifier.py (Task 6 §13-14, §54).

Trains yolo26n-cls.pt on datasets/specialists/snake/ (SNAKE-EXP-001).
Refuses to start if there isn't at least a minimal amount of data per
class — never trains on a near-empty or single-class dataset and
calls the result a classifier (Task 6 §53).

Usage:
    python scripts/specialists/train_snake_classifier.py [--min-per-class 10]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

CONFIG_PATH = Path("configs/specialists/snake.yaml")
DATASET_ROOT = Path("datasets/specialists/snake")


def count_samples() -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for split in ("train", "val", "test"):
        split_dir = DATASET_ROOT / split
        counts[split] = {}
        if not split_dir.exists():
            continue
        for category_dir in split_dir.iterdir():
            if category_dir.is_dir():
                images = [p for p in category_dir.glob("*") if p.is_file() and p.name != ".gitkeep"]
                counts[split][category_dir.name] = len(images)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the snake specialist classifier (Task 6).")
    parser.add_argument("--min-per-class", type=int, default=10)
    args = parser.parse_args()

    print("=" * 60)
    print("AI-CCTV Sentinel — Snake Specialist Classifier Training")
    print("=" * 60)

    if not CONFIG_PATH.exists():
        print(f"PENDING — {CONFIG_PATH} not found.")
        sys.exit(1)
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))

    counts = count_samples()
    train_counts = counts.get("train", {})
    total_train = sum(train_counts.values())

    print(f"Train samples by category: {train_counts}")

    if total_train == 0:
        print()
        print("PENDING — 0 training crops exist. Run create_snake_crops.py first.")
        sys.exit(1)

    under_threshold = {c: n for c, n in train_counts.items() if n < args.min_per_class}
    if under_threshold:
        print()
        print(
            f"PENDING — insufficient training data (< {args.min_per_class}/class): {under_threshold}. "
            "Per Task 6 §53, this is not trained on with fabricated/duplicated data."
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
    experiment_dir = Path("runs/specialists/snake") / config["experiment_id"]
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
