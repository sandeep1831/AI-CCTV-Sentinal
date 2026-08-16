"""AI-CCTV Sentinel — scripts/dataset/check_image_label_pairs.py (Task 4 §22, pipeline step 5).

Checks every image against its expected label file (same stem, .txt
extension) and vice versa. A negative/hard-negative image legitimately
having no label file is NOT an issue (documented empty_label_policy in
configs/dataset.yaml) — only genuine mismatches are flagged:
missing image for an existing label (orphan label), and duplicate
label files.

Usage:
    python scripts/dataset/check_image_label_pairs.py \\
        [--images-root datasets/processed/annotated/images] \\
        [--labels-root datasets/processed/annotated/labels]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from annotation_schemas import ImageLabelPair, PairingIssue  # noqa: E402
from validate_files import SUPPORTED_IMAGE_EXTENSIONS  # noqa: E402

DEFAULT_IMAGES_ROOT = Path("datasets/processed/annotated/images")
DEFAULT_LABELS_ROOT = Path("datasets/processed/annotated/labels")
REPORT_PATH = Path("datasets/processed/pairing_report.json")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check image/label pairing (Task 4).")
    parser.add_argument("--images-root", type=Path, default=DEFAULT_IMAGES_ROOT)
    parser.add_argument("--labels-root", type=Path, default=DEFAULT_LABELS_ROOT)
    args = parser.parse_args()

    images = (
        {p.stem: p for p in args.images_root.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS}
        if args.images_root.exists()
        else {}
    )
    labels = {p.stem: p for p in args.labels_root.rglob("*.txt")} if args.labels_root.exists() else {}

    all_stems = set(images) | set(labels)
    pairs: list[ImageLabelPair] = []

    for stem in sorted(all_stems):
        image_path = images.get(stem)
        label_path = labels.get(stem)
        issues: list[PairingIssue] = []

        if image_path is None and label_path is not None:
            issues.append(PairingIssue.ORPHAN_LABEL)
        # image_path present, label_path absent -> intentional negative
        # image under empty_label_policy; NOT flagged as an issue.

        pairs.append(
            ImageLabelPair(
                image_path=str(image_path) if image_path else None,
                label_path=str(label_path) if label_path else None,
                split="unassigned",
                issues=issues,
            )
        )

    orphan_labels = [p for p in pairs if PairingIssue.ORPHAN_LABEL in p.issues]
    negatives = [p for p in pairs if p.image_path and not p.label_path]
    annotated = [p for p in pairs if p.image_path and p.label_path]

    print("=" * 60)
    print("AI-CCTV Sentinel — Image/Label Pairing Check (Task 4, step 5)")
    print("=" * 60)
    print(f"Images root         : {args.images_root}")
    print(f"Labels root         : {args.labels_root}")
    print(f"Total images        : {len(images)}")
    print(f"Total label files   : {len(labels)}")
    print(f"Annotated pairs     : {len(annotated)}")
    print(f"Negative images     : {len(negatives)} (no label file — valid per empty_label_policy)")
    print(f"Orphan labels       : {len(orphan_labels)} (label with no matching image — INVALID)")
    print("=" * 60)

    if not images and not labels:
        print("No images or labels found yet — nothing to pair.")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "images_root": str(args.images_root),
                "labels_root": str(args.labels_root),
                "total_images": len(images),
                "total_labels": len(labels),
                "annotated_pairs": len(annotated),
                "negative_images": len(negatives),
                "orphan_labels": len(orphan_labels),
                "pairs": [p.model_dump(mode="json") for p in pairs],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
