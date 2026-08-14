"""AI-CCTV Sentinel — scripts/dataset/validate_images.py (Task 4 §23-25, pipeline step 1).

Validates every image under the annotation staging area
(datasets/processed/annotated/images/ by default — the output of
exporting from CVAT, before grouping/splitting/YOLO-build). Checks
readability, dimensions, and channel validity. Never assumes an
extension means a file is valid; never deletes anything.

Usage:
    python scripts/dataset/validate_images.py [--root datasets/processed/annotated/images]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_files import SUPPORTED_IMAGE_EXTENSIONS  # noqa: E402

DEFAULT_ROOT = Path("datasets/processed/annotated/images")
REPORT_PATH = Path("datasets/processed/validate_images_report.json")


def validate_image(path: Path) -> dict:
    result = {
        "path": str(path),
        "readable": False,
        "width": None,
        "height": None,
        "channels": None,
        "issues": [],
    }

    if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        result["issues"].append("unsupported_extension")
        return result

    if path.stat().st_size == 0:
        result["issues"].append("zero_byte_file")
        return result

    try:
        import cv2

        image = cv2.imread(str(path))
        if image is None:
            result["issues"].append("corrupt_or_unreadable")
            return result
        height, width = image.shape[:2]
        channels = image.shape[2] if image.ndim == 3 else 1
        result["readable"] = True
        result["width"] = width
        result["height"] = height
        result["channels"] = channels
        if width <= 0 or height <= 0:
            result["issues"].append("invalid_dimensions")
        if channels not in (1, 3, 4):
            result["issues"].append("invalid_channels")
    except Exception:  # noqa: BLE001
        result["issues"].append("corrupt_or_unreadable")

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate images before annotation processing (Task 4).")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()

    if not args.root.exists():
        files: list[Path] = []
    else:
        files = [p for p in args.root.rglob("*") if p.is_file() and not p.name.startswith(".")]

    results = [validate_image(p) for p in files]
    valid = [r for r in results if r["readable"] and not r["issues"]]
    invalid = [r for r in results if not (r["readable"] and not r["issues"])]

    print("=" * 60)
    print("AI-CCTV Sentinel — Image Validation (Task 4, step 1)")
    print("=" * 60)
    print(f"Root scanned  : {args.root}")
    print(f"Total images  : {len(results)}")
    print(f"Valid images  : {len(valid)}")
    print(f"Invalid images: {len(invalid)}")
    print("=" * 60)

    if not results:
        print(
            "No images found in the annotation staging area yet. This is "
            "expected until Task 3 sources are collected and exported from "
            "an annotation tool (CVAT) into "
            f"{DEFAULT_ROOT}. See docs/research/dataset-v1-report.md."
        )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "root": str(args.root),
                "total": len(results),
                "valid": len(valid),
                "invalid": len(invalid),
                "results": results,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
