"""AI-CCTV Sentinel — scripts/dataset/validate_files.py (Task 3 §39).

Scans datasets/raw/ for obviously bad files (corrupt, zero-byte,
unsupported extension, duplicate filename, invalid dimensions) and
produces a report. Never deletes anything — rejected files are only
reported and optionally quarantined (moved, not removed) for human
review, per Task 3 §39 and §47.

Usage:
    python scripts/dataset/validate_files.py [--root datasets/raw] [--quarantine]
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schemas import FileValidationResult, Quality, ValidationIssue  # noqa: E402

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}
SUPPORTED_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS | SUPPORTED_VIDEO_EXTENSIONS

DEFAULT_ROOT = Path("datasets/raw")
QUARANTINE_DIR = Path("datasets/quarantine")
REPORT_PATH = Path("datasets/metadata/validation_report.json")


def iter_candidate_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return [p for p in root.rglob("*") if p.is_file() and not p.name.startswith(".")]


def check_image(path: Path) -> tuple[bool, list[ValidationIssue]]:
    """Attempt to open an image with OpenCV; report corruption/dimension issues."""

    issues: list[ValidationIssue] = []
    try:
        import cv2

        image = cv2.imread(str(path))
        if image is None:
            issues.append(ValidationIssue.CORRUPT_IMAGE)
            return False, issues
        height, width = image.shape[:2]
        if height < 16 or width < 16:
            issues.append(ValidationIssue.INVALID_DIMENSIONS)
        return True, issues
    except Exception:  # noqa: BLE001
        issues.append(ValidationIssue.CORRUPT_IMAGE)
        return False, issues


def validate_file(path: Path, seen_filenames: Counter) -> FileValidationResult:
    issues: list[ValidationIssue] = []

    if path.stat().st_size == 0:
        issues.append(ValidationIssue.ZERO_BYTE_FILE)

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        issues.append(ValidationIssue.UNSUPPORTED_EXTENSION)

    seen_filenames[path.name] += 1
    if seen_filenames[path.name] > 1:
        issues.append(ValidationIssue.DUPLICATE_FILENAME)

    readable = True
    if path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS and ValidationIssue.ZERO_BYTE_FILE not in issues:
        readable, image_issues = check_image(path)
        issues.extend(image_issues)

    if readable and not issues:
        quality = Quality.GOOD
    elif readable and issues == [ValidationIssue.DUPLICATE_FILENAME]:
        quality = Quality.ACCEPTABLE
    else:
        quality = Quality.UNUSABLE

    return FileValidationResult(path=str(path), readable=readable, issues=issues, quality=quality)


def quarantine_file(path: Path, root: Path) -> Path:
    relative = path.relative_to(root)
    destination = QUARANTINE_DIR / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), str(destination))
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate raw dataset files (Task 3).")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument(
        "--quarantine",
        action="store_true",
        help="Move (not delete) invalid files into datasets/quarantine/ for review.",
    )
    args = parser.parse_args()

    files = iter_candidate_files(args.root)
    seen_filenames: Counter = Counter()
    results: list[FileValidationResult] = []

    for path in files:
        results.append(validate_file(path, seen_filenames))

    valid = [r for r in results if r.passed]
    invalid = [r for r in results if not r.passed]
    duplicates = [r for r in results if ValidationIssue.DUPLICATE_FILENAME in r.issues]

    if args.quarantine:
        for result in invalid:
            quarantine_file(Path(result.path), args.root)

    print("=" * 60)
    print("AI-CCTV Sentinel — Dataset File Validation")
    print("=" * 60)
    print(f"Root scanned     : {args.root}")
    print(f"Total files      : {len(results)}")
    print(f"Valid files      : {len(valid)}")
    print(f"Invalid files    : {len(invalid)}")
    print(f"Duplicate names  : {len(duplicates)}")
    if args.quarantine and invalid:
        print(f"Quarantined      : {len(invalid)} file(s) moved to {QUARANTINE_DIR}")
    print("=" * 60)

    if not results:
        print(
            "No files found under the scanned root. This is expected until real "
            "dataset sources are added under datasets/raw/ — see "
            "docs/research/dataset-gap-analysis.md."
        )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(args.root),
        "total_files": len(results),
        "valid_files": len(valid),
        "invalid_files": len(invalid),
        "duplicate_filenames": len(duplicates),
        "results": [r.model_dump(mode="json") for r in results],
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
