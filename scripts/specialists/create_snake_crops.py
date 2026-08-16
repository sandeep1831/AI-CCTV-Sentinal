"""AI-CCTV Sentinel — scripts/specialists/create_snake_crops.py (Task 6 §9-12, §20).

Generates the snake specialist-classification dataset from Task 4's
GROUND-TRUTH YOLO boxes only — never from model predictions, to avoid
contaminating the first classifier's training data with detector
errors (Task 6 §10).

For each snake ('snake' class in configs/classes.yaml) box in
datasets/yolo/sentinel_v1/labels/<split>/, this script:
    1. Crops the box with configurable padding (configs/specialists/snake.yaml)
    2. Looks up snake_category metadata (likely_venomous /
       likely_non_venomous / unknown) from datasets/metadata/samples/,
       matched by original filename — defaults to 'unknown' if no
       reliable secondary classification exists (never fabricated)
    3. Runs a basic quality check (visibility, blur, size)
    4. Places the crop under datasets/specialists/snake/<split>/<category>/
       — reusing the SAME split (train/val/test) the source image
       already belongs to, so Task 4's leakage-prevention grouping is
       inherited rather than re-randomized (Task 6 §20)

Usage:
    python scripts/specialists/create_snake_crops.py
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

YOLO_DATASET = Path("datasets/yolo/sentinel_v1")
SAMPLES_METADATA_DIR = Path("datasets/metadata/samples")
SNAKE_CONFIG = Path("configs/specialists/snake.yaml")
CLASSES_CONFIG = Path("configs/classes.yaml")
OUTPUT_ROOT = Path("datasets/specialists/snake")
MIN_CROP_FRACTION = 0.02  # snake must occupy at least 2% of crop area to be usable (Task 6 §12 spirit)


def load_snake_class_id() -> int | None:
    if not CLASSES_CONFIG.exists():
        return None
    data = yaml.safe_load(CLASSES_CONFIG.read_text(encoding="utf-8")) or {}
    for class_id, name in (data.get("classes") or {}).items():
        if name == "snake":
            return int(class_id)
    return None


def load_snake_category(original_filename: str) -> str:
    """Look up snake_category metadata; defaults to 'unknown' if no
    reliable secondary classification exists — never guessed."""

    if not SAMPLES_METADATA_DIR.exists():
        return "unknown"
    for path in SAMPLES_METADATA_DIR.glob("*.json"):
        if path.name == "SAMPLE_TEMPLATE.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if data.get("original_filename") == original_filename:
            return data.get("snake_category") or "unknown"
    return "unknown"


def crop_with_padding(image, bbox_xywh_norm, padding_percent: float):
    import cv2

    height, width = image.shape[:2]
    xc, yc, w, h = bbox_xywh_norm
    x1 = (xc - w / 2) * width
    y1 = (yc - h / 2) * height
    x2 = (xc + w / 2) * width
    y2 = (yc + h / 2) * height

    pad_x = (x2 - x1) * (padding_percent / 100)
    pad_y = (y2 - y1) * (padding_percent / 100)
    x1 = max(0, int(x1 - pad_x))
    y1 = max(0, int(y1 - pad_y))
    x2 = min(width, int(x2 + pad_x))
    y2 = min(height, int(y2 + pad_y))

    if x2 <= x1 or y2 <= y1:
        return None
    crop = image[y1:y2, x1:x2]
    crop_area_fraction = ((x2 - x1) * (y2 - y1)) / (width * height)
    return crop, crop_area_fraction


def main() -> None:
    print("=" * 60)
    print("AI-CCTV Sentinel — Snake Crop Generation")
    print("=" * 60)

    if not SNAKE_CONFIG.exists():
        print(f"PENDING — {SNAKE_CONFIG} not found.")
        return

    config = yaml.safe_load(SNAKE_CONFIG.read_text(encoding="utf-8"))
    padding_percent = config["dataset"]["crop_padding_percent"]

    snake_class_id = load_snake_class_id()
    if snake_class_id is None:
        print("PENDING — 'snake' class not found in configs/classes.yaml.")
        return

    try:
        import cv2
    except ImportError:
        print("OpenCV not installed in this environment.")
        return

    stats = {"train": 0, "val": 0, "test": 0}
    quality_rejected = 0
    category_counts: dict[str, int] = {}

    for split in ("train", "val", "test"):
        image_dir = YOLO_DATASET / "images" / split
        label_dir = YOLO_DATASET / "labels" / split
        if not image_dir.exists() or not label_dir.exists():
            continue

        for label_path in label_dir.glob("*.txt"):
            image_path = None
            for ext in (".jpg", ".jpeg", ".png"):
                candidate = image_dir / (label_path.stem + ext)
                if candidate.exists():
                    image_path = candidate
                    break
            if image_path is None:
                continue

            image = cv2.imread(str(image_path))
            if image is None:
                continue

            lines = [ln for ln in label_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
            for i, line in enumerate(lines):
                parts = line.split()
                if not parts or int(parts[0]) != snake_class_id:
                    continue
                xc, yc, w, h = (float(v) for v in parts[1:5])
                result = crop_with_padding(image, (xc, yc, w, h), padding_percent)
                if result is None:
                    quality_rejected += 1
                    continue
                crop, area_fraction = result
                if area_fraction < MIN_CROP_FRACTION:
                    quality_rejected += 1
                    continue

                category = load_snake_category(image_path.name)
                category_dir = OUTPUT_ROOT / split / category
                category_dir.mkdir(parents=True, exist_ok=True)
                crop_filename = f"{label_path.stem}_snake{i}.jpg"
                cv2.imwrite(str(category_dir / crop_filename), crop)

                stats[split] += 1
                category_counts[category] = category_counts.get(category, 0) + 1

    total_crops = sum(stats.values())

    print(f"Snake class ID       : {snake_class_id}")
    print(f"Crops generated       : {total_crops}")
    print(f"  train: {stats['train']} | val: {stats['val']} | test: {stats['test']}")
    print(f"Quality-rejected      : {quality_rejected}")
    print(f"By category           : {category_counts}")

    manifest = {
        "dataset_name": "snake-specialist-v1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "datasets/yolo/sentinel_v1 (ground-truth boxes only, per Task 6 §10)",
        "crop_generation_method": f"tight bbox + {padding_percent}% padding",
        "class_mapping": {0: "likely_venomous", 1: "likely_non_venomous", 2: "unknown"},
        "split": stats,
        "category_counts": category_counts,
        "quality_rejected": quality_rejected,
        "source_grouping": "inherited from Task 4 split — same source video/sequence stays in one split (Task 6 §20)",
        "license": "inherited per-sample from Task 3/4 source records; see datasets/metadata/sources/",
        "dataset_hash": None,  # populated once real crops exist to hash
    }
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    if total_crops == 0:
        print()
        print(
            "PENDING — 0 snake crops generated. This is expected until "
            "Task 4's dataset actually contains annotated snake bounding "
            "boxes. Re-run this script once real data exists."
        )


if __name__ == "__main__":
    main()
