"""AI-CCTV Sentinel — scripts/dataset/check_bbox_coordinates.py (Task 4 §21, pipeline step 4).

Focused report on bounding-box geometry only: normalized coordinate
ranges, positive width/height, and whether the converted box stays
within image bounds. Reuses validate_yolo_labels.py's parser.

Usage:
    python scripts/dataset/check_bbox_coordinates.py [--root datasets/processed/annotated/labels]
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from annotation_schemas import LabelIssue  # noqa: E402
from validate_yolo_labels import DEFAULT_ROOT, load_valid_class_ids, validate_label_file  # noqa: E402

GEOMETRY_ISSUES = {
    LabelIssue.X_CENTER_OUT_OF_RANGE,
    LabelIssue.Y_CENTER_OUT_OF_RANGE,
    LabelIssue.WIDTH_OUT_OF_RANGE,
    LabelIssue.HEIGHT_OUT_OF_RANGE,
    LabelIssue.NON_POSITIVE_WIDTH,
    LabelIssue.NON_POSITIVE_HEIGHT,
    LabelIssue.BOX_EXCEEDS_IMAGE_BOUNDS,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Check bounding-box coordinate validity (Task 4).")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()

    valid_class_ids = load_valid_class_ids()
    label_files = sorted(args.root.rglob("*.txt")) if args.root.exists() else []

    total_boxes = 0
    geometry_issue_counts: Counter[str] = Counter()
    files_with_geometry_issues = 0

    for path in label_files:
        result = validate_label_file(path, valid_class_ids)
        total_boxes += len(result.boxes)
        file_geometry_issues = [i for i in result.issues if i in GEOMETRY_ISSUES]
        if file_geometry_issues:
            files_with_geometry_issues += 1
        for issue in file_geometry_issues:
            geometry_issue_counts[issue.value] += 1

    print("=" * 60)
    print("AI-CCTV Sentinel — Bounding Box Coordinate Check (Task 4, step 4)")
    print("=" * 60)
    print(f"Root scanned              : {args.root}")
    print(f"Label files scanned       : {len(label_files)}")
    print(f"Total boxes               : {total_boxes}")
    print(f"Files with geometry issues: {files_with_geometry_issues}")
    if geometry_issue_counts:
        for issue, count in geometry_issue_counts.most_common():
            print(f"  {issue:<30}: {count}")
    else:
        print("  none")
    print("=" * 60)

    if not label_files:
        print("No label files found yet — nothing to check.")


if __name__ == "__main__":
    main()
