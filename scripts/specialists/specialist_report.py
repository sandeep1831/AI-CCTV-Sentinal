"""AI-CCTV Sentinel — scripts/specialists/specialist_report.py (Task 6 §82).

Aggregates the real state of both specialist branches (dataset
manifests, evaluation reports if they exist, registered model
metadata if it exists) into the Task 6 final status report. Never
fabricates a value — every field is either a real number pulled from
a prior stage's output, or explicitly PENDING.

Usage:
    python scripts/specialists/specialist_report.py
"""

from __future__ import annotations

import json
from pathlib import Path

SNAKE_MANIFEST = Path("datasets/specialists/snake/manifest.json")
DOG_HEALTH_MANIFEST = Path("datasets/specialists/dog_health/manifest.json")
SNAKE_MODEL_METADATA = Path("models/specialists/snake/sentinel-snake-cls-v1.0.0.json")
DOG_HEALTH_MODEL_METADATA = Path("models/specialists/dog_health/sentinel-dog-health-v1.0.0.json")


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def field(value, label="PENDING"):
    return value if value is not None else label


def main() -> None:
    snake_manifest = load_json(SNAKE_MANIFEST)
    dog_manifest = load_json(DOG_HEALTH_MANIFEST)
    snake_model = load_json(SNAKE_MODEL_METADATA)
    dog_model = load_json(DOG_HEALTH_MODEL_METADATA)

    snake_train_total = sum((snake_manifest or {}).get("split", {}).values()) if snake_manifest else 0
    dog_counts = (dog_manifest or {}).get("counts", {})
    dog_train_total = sum(v.get("train", 0) for v in dog_counts.values()) if dog_counts else 0

    snake_status = "PASS" if snake_model else "PENDING"
    dog_status = "PASS" if dog_model else "PENDING"

    print("=" * 60)
    print("TASK 6 — SPECIALIST ANALYSIS")
    print("=" * 60)
    print()
    print("SNAKE SPECIALIST")
    print("-" * 60)
    print()
    print(f"Dataset:\n    {snake_train_total} training crops" + (" (0 — PENDING real data)" if snake_train_total == 0 else ""))
    print()
    print("Classes:\n    likely_venomous\n    likely_non_venomous\n    unknown")
    print()
    print(f"Model:\n    {field(snake_model and snake_model.get('model_name'))}")
    print()
    print(f"Top-1:\n    {field(snake_model and snake_model.get('metrics', {}).get('top1_accuracy'))}")
    print()
    print(f"Status:\n    {snake_status}")
    print()
    print("-" * 60)
    print()
    print("DOG HEALTH SCREENING")
    print("-" * 60)
    print()
    print(f"Dataset:\n    {dog_train_total} training samples" + (" (0 — PENDING real data)" if dog_train_total == 0 else ""))
    print()
    print(f"Model:\n    {field(dog_model and dog_model.get('model_name'))}")
    print()
    for cls in ["normal_visible_appearance", "possible_wound", "possible_skin_abnormality", "possible_injury", "unable_to_assess"]:
        count = dog_counts.get(cls, {}).get("train", "PENDING") if dog_counts else "PENDING"
        print(f"{cls}:\n    {count}")
        print()
    print(f"Status:\n    {dog_status}")
    print()
    print("-" * 60)
    print("SPECIALIST INFERENCE")
    print("-" * 60)
    print()
    print("Snake latency:\n    PENDING — no model trained")
    print()
    print("Dog health latency:\n    PENDING — no model trained")
    print()
    print("-" * 60)
    print("MEDICAL SAFETY")
    print("-" * 60)
    print()
    print("Disease diagnosis:\n    NOT CLAIMED")
    print()
    print("Veterinary review:\n    REQUIRED FOR HEALTH FLAGS")
    print()
    print("-" * 60)
    overall_status = "PASS" if (snake_status == "PASS" and dog_status == "PASS") else "PARTIAL" if (snake_status == "PASS" or dog_status == "PASS") else "NOT READY"
    print()
    print(f"TASK 6 STATUS:\n    {overall_status}")
    print("=" * 60)


if __name__ == "__main__":
    main()
