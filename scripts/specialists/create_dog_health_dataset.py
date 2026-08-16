"""AI-CCTV Sentinel — scripts/specialists/create_dog_health_dataset.py (Task 6 §25-27, §49).

Builds the dog visible-health screening dataset from a staging area of
already-licensed, already-labeled source images. This project does
NOT auto-generate dog-health labels from CCTV detections the way
create_snake_crops.py does for snakes — health labels require an
actual human/veterinary-sourced judgment per Task 6 §26-27, so this
script only ORGANIZES pre-labeled staged data, it never invents a
label.

Expected staging layout (git-ignored, populated by a human curator):

    datasets/specialists/dog_health/_incoming/
    ├── <sample_id>.jpg
    └── <sample_id>.json   # {"category": "possible_wound", "visibility": "full_body_visible",
                            #  "source": "...", "license": "...", "encounter_id": "..."}

For each valid pair, this script:
    1. Validates the category is one of the 5 approved classes
    2. Groups by encounter_id (same dog encounter -> same split, Task 6 §49)
    3. Copies into datasets/specialists/dog_health/<split>/<category>/
    4. Writes manifest.json with real counts only

If the _incoming/ staging area is empty or contains too few samples
per class, this script explicitly reports PENDING — it does NOT lower
the bar or fabricate data (Task 6 §52, §81).

Usage:
    python scripts/specialists/create_dog_health_dataset.py [--min-per-class 20]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

DOG_HEALTH_CONFIG = Path("configs/specialists/dog_health.yaml")
INCOMING_DIR = Path("datasets/specialists/dog_health/_incoming")
OUTPUT_ROOT = Path("datasets/specialists/dog_health")
APPROVED_CLASSES = {
    "normal_visible_appearance",
    "possible_wound",
    "possible_skin_abnormality",
    "possible_injury",
    "unable_to_assess",
}
APPROVED_VISIBILITY = {"full_body_visible", "partial_body_visible", "insufficient_visibility"}


def assign_split(encounter_id: str, sample_id: str) -> str:
    """Deterministic, source-aware split assignment (Task 6 §49): the
    same encounter always maps to the same split, via a stable hash —
    not random-per-file."""

    key = encounter_id or sample_id
    digest = int(hashlib.sha256(key.encode("utf-8")).hexdigest(), 16)
    bucket = digest % 100
    if bucket < 70:
        return "train"
    if bucket < 85:
        return "val"
    return "test"


def _write_manifest(counts: dict, rejected: int, status: str) -> None:
    manifest = {
        "dataset_name": "dog-health-v1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "licensed/authorized staged images only (Task 6 §26)",
        "annotation_method": "human/veterinary-sourced category label per sample, staged via _incoming/",
        "class_mapping": {
            0: "normal_visible_appearance",
            1: "possible_wound",
            2: "possible_skin_abnormality",
            3: "possible_injury",
            4: "unable_to_assess",
        },
        "visibility_policy": "insufficient_visibility forces category=unable_to_assess (Task 6 §31)",
        "counts": counts,
        "rejected": rejected,
        "license": "per-sample; recorded in each staged sample's JSON, never invented",
        "status": status,
    }
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the dog health screening dataset (Task 6).")
    parser.add_argument(
        "--min-per-class",
        type=int,
        default=20,
        help="Minimum labeled samples required per abnormality class before the branch is considered trainable.",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("AI-CCTV Sentinel — Dog Health Dataset Builder")
    print("=" * 60)

    if not INCOMING_DIR.exists() or not any(INCOMING_DIR.glob("*.json")):
        print(f"PENDING — no staged, labeled data found in {INCOMING_DIR}/")
        print(
            "Per Task 6 §26-27, dog health labels require a real "
            "human/veterinary-sourced judgment. Stage licensed, labeled "
            "images there (see this script's docstring for the expected "
            "<sample_id>.jpg + <sample_id>.json pair format) before "
            "re-running this script."
        )
        _write_manifest(counts={}, rejected=0, status="PENDING — no staged data")
        return

    counts: dict[str, dict[str, int]] = {c: {"train": 0, "val": 0, "test": 0} for c in APPROVED_CLASSES}
    rejected = 0

    for label_path in sorted(INCOMING_DIR.glob("*.json")):
        sample_id = label_path.stem
        image_path = None
        for ext in (".jpg", ".jpeg", ".png"):
            candidate = INCOMING_DIR / f"{sample_id}{ext}"
            if candidate.exists():
                image_path = candidate
                break
        if image_path is None:
            rejected += 1
            continue

        try:
            meta = json.loads(label_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            rejected += 1
            continue

        category = meta.get("category")
        visibility = meta.get("visibility")
        if category not in APPROVED_CLASSES or visibility not in APPROVED_VISIBILITY:
            rejected += 1
            continue

        # Visibility policy override (Task 6 §31): insufficient
        # visibility always forces unable_to_assess, regardless of the
        # curator's category label.
        if visibility == "insufficient_visibility":
            category = "unable_to_assess"

        encounter_id = meta.get("encounter_id", sample_id)
        split = assign_split(encounter_id, sample_id)

        dest_dir = OUTPUT_ROOT / split / category
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(image_path, dest_dir / image_path.name)
        counts[category][split] += 1

    total = sum(sum(v.values()) for v in counts.values())
    print(f"Samples organized : {total}")
    print(f"Rejected (invalid label/missing pair) : {rejected}")
    for category, splits in counts.items():
        print(f"  {category:<28}: train={splits['train']} val={splits['val']} test={splits['test']}")

    under_threshold = {
        c: sum(v.values()) for c, v in counts.items() if sum(v.values()) < args.min_per_class
    }
    status = "READY" if not under_threshold else f"PENDING — under {args.min_per_class}/class: {under_threshold}"

    _write_manifest(counts=counts, rejected=rejected, status=status)

    print()
    print(f"Status: {status}")
    if under_threshold:
        print(
            "Per Task 6 §52/§81: classes below the minimum sample count "
            "are NOT trained on with fabricated/duplicated data. Collect "
            "more real, licensed, labeled samples for these classes."
        )


if __name__ == "__main__":
    main()
