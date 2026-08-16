"""AI-CCTV Sentinel — scripts/dataset/build_yolo_dataset.py (Task 4 §15, pipeline step 10).

Copies (never moves — datasets/raw/ and datasets/processed/annotated/
are never mutated, per Task 4 §49) each annotated image and its label
(if any) into datasets/yolo/sentinel_v1/images/<split>/ and
labels/<split>/, according to the group->split assignment from
create_dataset_split.py. A negative image with no label file is
copied with no corresponding label, per the documented
empty_label_policy.

Usage:
    python scripts/dataset/build_yolo_dataset.py
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_files import SUPPORTED_IMAGE_EXTENSIONS  # noqa: E402

IMAGES_ROOT = Path("datasets/processed/annotated/images")
LABELS_ROOT = Path("datasets/processed/annotated/labels")
SPLIT_REPORT = Path("datasets/processed/split_assignments.json")
GROUPS_REPORT = Path("datasets/processed/group_assignments.json")
OUTPUT_ROOT = Path("datasets/yolo/sentinel_v1")
REPORT_PATH = Path("datasets/processed/build_yolo_dataset_report.json")


def load_group_to_split() -> dict[str, str]:
    if not SPLIT_REPORT.exists():
        return {}
    data = json.loads(SPLIT_REPORT.read_text(encoding="utf-8"))
    return {a["group_id"]: a["split"] for a in data.get("assignments", [])}


def load_path_to_group() -> dict[str, str]:
    if not GROUPS_REPORT.exists():
        return {}
    data = json.loads(GROUPS_REPORT.read_text(encoding="utf-8"))
    return {a["path"]: a["group_id"] for a in data.get("assignments", [])}


def main() -> None:
    group_to_split = load_group_to_split()
    path_to_group = load_path_to_group()

    for split in ("train", "val", "test"):
        (OUTPUT_ROOT / "images" / split).mkdir(parents=True, exist_ok=True)
        (OUTPUT_ROOT / "labels" / split).mkdir(parents=True, exist_ok=True)

    if not group_to_split or not path_to_group:
        print("=" * 60)
        print("AI-CCTV Sentinel — Build YOLO Dataset (Task 4, step 10)")
        print("=" * 60)
        print(
            "PENDING — no split assignments available. Run "
            "create_group_ids.py then create_dataset_split.py first."
        )
        print("=" * 60)
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(
            json.dumps(
                {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "status": "PENDING",
                    "images_copied": 0,
                    "labels_copied": 0,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return

    images_copied = {"train": 0, "val": 0, "test": 0}
    labels_copied = {"train": 0, "val": 0, "test": 0}

    for image_path_str, group_id in path_to_group.items():
        image_path = Path(image_path_str)
        if not image_path.exists() or image_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            continue
        split = group_to_split.get(group_id)
        if split is None:
            continue

        dest_image = OUTPUT_ROOT / "images" / split / image_path.name
        shutil.copy2(image_path, dest_image)
        images_copied[split] += 1

        label_path = LABELS_ROOT / f"{image_path.stem}.txt"
        if label_path.exists():
            dest_label = OUTPUT_ROOT / "labels" / split / label_path.name
            shutil.copy2(label_path, dest_label)
            labels_copied[split] += 1
        # else: negative image, no label copied — valid per empty_label_policy.

    total_images = sum(images_copied.values())
    total_labels = sum(labels_copied.values())

    print("=" * 60)
    print("AI-CCTV Sentinel — Build YOLO Dataset (Task 4, step 10)")
    print("=" * 60)
    print(f"Output root    : {OUTPUT_ROOT}")
    print(f"Images copied  : train={images_copied['train']}, val={images_copied['val']}, test={images_copied['test']} (total {total_images})")
    print(f"Labels copied  : train={labels_copied['train']}, val={labels_copied['val']}, test={labels_copied['test']} (total {total_labels})")
    print("=" * 60)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "status": "OK",
                "output_root": str(OUTPUT_ROOT),
                "images_copied": images_copied,
                "labels_copied": labels_copied,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
