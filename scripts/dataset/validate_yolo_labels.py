"""AI-CCTV Sentinel — scripts/dataset/validate_yolo_labels.py (Task 4 §19, pipeline step 2).

Validates every YOLO-format .txt label file: field count, numeric
values, class ID range, normalized coordinate ranges, and positive
width/height. Never silently modifies a label — only reports.

Usage:
    python scripts/dataset/validate_yolo_labels.py [--root datasets/processed/annotated/labels]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yaml  # noqa: E402
from annotation_schemas import LabelFileValidationResult, LabelIssue, YoloBoxLabel  # noqa: E402

DEFAULT_ROOT = Path("datasets/processed/annotated/labels")
CLASSES_CONFIG = Path("configs/classes.yaml")
REPORT_PATH = Path("datasets/processed/validate_labels_report.json")


def load_valid_class_ids() -> set[int]:
    if not CLASSES_CONFIG.exists():
        return set()
    data = yaml.safe_load(CLASSES_CONFIG.read_text(encoding="utf-8")) or {}
    return {int(k) for k in (data.get("classes") or {})}


def parse_and_validate_line(line: str, valid_class_ids: set[int]) -> tuple[YoloBoxLabel | None, list[LabelIssue]]:
    issues: list[LabelIssue] = []
    parts = line.strip().split()

    if len(parts) != 5:
        return None, [LabelIssue.WRONG_FIELD_COUNT]

    try:
        class_id = int(parts[0])
        x_center, y_center, width, height = (float(p) for p in parts[1:])
    except ValueError:
        return None, [LabelIssue.NON_NUMERIC_VALUE]

    if valid_class_ids and class_id not in valid_class_ids:
        issues.append(LabelIssue.INVALID_CLASS_ID)

    if not (0.0 <= x_center <= 1.0):
        issues.append(LabelIssue.X_CENTER_OUT_OF_RANGE)
    if not (0.0 <= y_center <= 1.0):
        issues.append(LabelIssue.Y_CENTER_OUT_OF_RANGE)
    if not (0.0 < width <= 1.0):
        issues.append(LabelIssue.WIDTH_OUT_OF_RANGE)
        if width <= 0:
            issues.append(LabelIssue.NON_POSITIVE_WIDTH)
    if not (0.0 < height <= 1.0):
        issues.append(LabelIssue.HEIGHT_OUT_OF_RANGE)
        if height <= 0:
            issues.append(LabelIssue.NON_POSITIVE_HEIGHT)

    box = YoloBoxLabel(class_id=class_id, x_center=x_center, y_center=y_center, width=width, height=height)

    x_min, y_min, x_max, y_max = box.to_corners()
    if x_min < 0 or y_min < 0 or x_max > 1 or y_max > 1:
        issues.append(LabelIssue.BOX_EXCEEDS_IMAGE_BOUNDS)

    return box, issues


def validate_label_file(path: Path, valid_class_ids: set[int]) -> LabelFileValidationResult:
    boxes: list[YoloBoxLabel] = []
    file_issues: list[LabelIssue] = []

    text = path.read_text(encoding="utf-8").strip()
    if not text:
        # An explicitly empty label file (as opposed to a missing one).
        # Not itself an error under this project's empty_label_policy,
        # but recorded with zero boxes.
        return LabelFileValidationResult(label_path=str(path), boxes=[], issues=[])

    for line in text.splitlines():
        if not line.strip():
            continue
        box, issues = parse_and_validate_line(line, valid_class_ids)
        if box is not None:
            boxes.append(box)
        file_issues.extend(issues)

    return LabelFileValidationResult(label_path=str(path), boxes=boxes, issues=file_issues)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate YOLO label files (Task 4).")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()

    valid_class_ids = load_valid_class_ids()
    label_files = sorted(args.root.rglob("*.txt")) if args.root.exists() else []

    results = [validate_label_file(p, valid_class_ids) for p in label_files]
    valid = [r for r in results if r.is_valid]
    invalid = [r for r in results if not r.is_valid]
    total_boxes = sum(len(r.boxes) for r in results)

    print("=" * 60)
    print("AI-CCTV Sentinel — YOLO Label Validation (Task 4, step 2)")
    print("=" * 60)
    print(f"Root scanned    : {args.root}")
    print(f"Valid class IDs : {sorted(valid_class_ids) if valid_class_ids else 'PENDING — configs/classes.yaml not found'}")
    print(f"Label files     : {len(results)}")
    print(f"Valid files     : {len(valid)}")
    print(f"Invalid files   : {len(invalid)}")
    print(f"Total boxes     : {total_boxes}")
    print("=" * 60)

    if not results:
        print(
            "No label files found yet. This is expected until annotation "
            "(CVAT export) has actually produced YOLO .txt files under "
            f"{DEFAULT_ROOT}."
        )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "root": str(args.root),
                "valid_class_ids": sorted(valid_class_ids),
                "total_files": len(results),
                "valid_files": len(valid),
                "invalid_files": len(invalid),
                "total_boxes": total_boxes,
                "results": [r.model_dump(mode="json") for r in results],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
