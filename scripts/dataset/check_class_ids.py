"""AI-CCTV Sentinel — scripts/dataset/check_class_ids.py (Task 4 §20, pipeline step 3).

Focused report on class-ID validity only: which class IDs appear in
the label set, and which (if any) fall outside configs/classes.yaml.
Reuses the parsing logic in validate_yolo_labels.py rather than
duplicating it.

Usage:
    python scripts/dataset/check_class_ids.py [--root datasets/processed/annotated/labels]
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_yolo_labels import DEFAULT_ROOT, load_valid_class_ids, validate_label_file  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Check class-ID validity across all labels (Task 4).")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()

    valid_class_ids = load_valid_class_ids()
    label_files = sorted(args.root.rglob("*.txt")) if args.root.exists() else []

    class_id_counts: Counter[int] = Counter()
    invalid_class_ids: Counter[int] = Counter()

    for path in label_files:
        result = validate_label_file(path, valid_class_ids)
        for box in result.boxes:
            class_id_counts[box.class_id] += 1
            if valid_class_ids and box.class_id not in valid_class_ids:
                invalid_class_ids[box.class_id] += 1

    print("=" * 60)
    print("AI-CCTV Sentinel — Class ID Check (Task 4, step 3)")
    print("=" * 60)
    print(f"Root scanned         : {args.root}")
    print(f"Approved class IDs   : {sorted(valid_class_ids) if valid_class_ids else 'PENDING — configs/classes.yaml missing'}")
    print(f"Class IDs observed   : {dict(sorted(class_id_counts.items()))}")
    print(f"Invalid class IDs    : {dict(sorted(invalid_class_ids.items())) if invalid_class_ids else 'none'}")
    print("=" * 60)

    if not label_files:
        print("No label files found yet — nothing to check.")


if __name__ == "__main__":
    main()
