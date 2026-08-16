"""AI-CCTV Sentinel — scripts/dataset/inspect_dataset.py (Task 3 §38).

A fast, read-only structural inspection of the datasets/ tree: what
directories exist, how many files sit in each, and total size. This
is a lighter-weight companion to dataset_report.py (which requires
sample-level metadata to have been recorded) — inspect_dataset.py
works from the filesystem alone and is useful as a first sanity check
after adding new raw files.

Usage:
    python scripts/dataset/inspect_dataset.py [--root datasets]
"""

from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_ROOT = Path("datasets")
IGNORED_NAMES = {".gitkeep", ".DS_Store"}


def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"


def inspect_directory(path: Path) -> tuple[int, int]:
    """Return (file_count, total_bytes) for all real files under path."""

    file_count = 0
    total_bytes = 0
    if not path.exists():
        return 0, 0
    for item in path.rglob("*"):
        if item.is_file() and item.name not in IGNORED_NAMES:
            file_count += 1
            total_bytes += item.stat().st_size
    return file_count, total_bytes


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect the datasets/ directory tree (Task 3).")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()

    sections = [
        "raw/public",
        "raw/regional",
        "raw/cctv_like",
        "raw/staged",
        "raw/hard_negatives",
        "raw/environment/low_light",
        "raw/environment/rain",
        "raw/feedback/confirmed",
        "raw/feedback/false_positive",
        "raw/feedback/uncertain",
        "metadata/sources",
        "metadata/samples",
        "metadata/licenses",
        "processed",
        "annotations",
        "versions",
    ]

    print("=" * 60)
    print("AI-CCTV SENTINEL — DATASET STRUCTURAL INSPECTION")
    print("=" * 60)

    grand_total_files = 0
    grand_total_bytes = 0

    for section in sections:
        section_path = args.root / section
        file_count, total_bytes = inspect_directory(section_path)
        grand_total_files += file_count
        grand_total_bytes += total_bytes
        status = "empty" if file_count == 0 else f"{file_count} file(s), {human_size(total_bytes)}"
        exists = "" if section_path.exists() else "  [missing]"
        print(f"{section:<32}: {status}{exists}")

    print("-" * 60)
    print(f"{'TOTAL':<32}: {grand_total_files} file(s), {human_size(grand_total_bytes)}")
    print("=" * 60)

    if grand_total_files == 0:
        print(
            "No raw data files present yet. This is expected — Task 3 "
            "builds the collection/curation FOUNDATION; see "
            "docs/research/dataset-gap-analysis.md for what is PENDING."
        )


if __name__ == "__main__":
    main()
