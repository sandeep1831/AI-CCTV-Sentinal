"""AI-CCTV Sentinel — scripts/dataset/calculate_hashes.py (Task 3 §17, §40).

Computes SHA-256 (exact duplicate detection) and, for images, a
perceptual hash (near-duplicate detection) for every file under a
dataset root. Writes results to datasets/metadata/hashes.json and
flags exact-duplicate groups. Never deletes files.

Perceptual hashing uses a simple, dependency-light average-hash
implementation (no extra package required beyond OpenCV/NumPy, which
are already part of the Task 1 environment) so this script has no new
external dependency.

Usage:
    python scripts/dataset/calculate_hashes.py [--root datasets/raw]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_files import SUPPORTED_IMAGE_EXTENSIONS, iter_candidate_files  # noqa: E402

DEFAULT_ROOT = Path("datasets/raw")
REPORT_PATH = Path("datasets/metadata/hashes.json")


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def average_hash(path: Path, hash_size: int = 8) -> str | None:
    """Lightweight perceptual hash: resize to hash_size x hash_size
    grayscale, threshold against the mean, pack bits into a hex string.
    Not a substitute for a dedicated perceptual-hashing library, but
    sufficient to flag likely near-duplicates for human review.
    """

    try:
        import cv2
        import numpy as np

        image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            return None
        resized = cv2.resize(image, (hash_size, hash_size), interpolation=cv2.INTER_AREA)
        mean = resized.mean()
        bits = (resized > mean).flatten()
        value = 0
        for bit in bits:
            value = (value << 1) | int(bit)
        return f"{value:0{hash_size * hash_size // 4}x}"
    except Exception:  # noqa: BLE001
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute file hashes for duplicate detection (Task 3).")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()

    files = iter_candidate_files(args.root)
    records: list[dict] = []
    sha_groups: dict[str, list[str]] = defaultdict(list)

    for path in files:
        sha256 = sha256_of(path)
        phash = average_hash(path) if path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS else None
        records.append({"path": str(path), "sha256": sha256, "phash": phash})
        sha_groups[sha256].append(str(path))

    exact_duplicate_groups = {h: paths for h, paths in sha_groups.items() if len(paths) > 1}

    print("=" * 60)
    print("AI-CCTV Sentinel — Dataset Hash Calculation")
    print("=" * 60)
    print(f"Root scanned            : {args.root}")
    print(f"Files hashed             : {len(records)}")
    print(f"Exact-duplicate groups   : {len(exact_duplicate_groups)}")
    print(f"Exact-duplicate files    : {sum(len(v) for v in exact_duplicate_groups.values())}")
    print("=" * 60)

    if not records:
        print(
            "No files found to hash. This is expected until real dataset "
            "sources are added under datasets/raw/."
        )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(args.root),
        "file_count": len(records),
        "exact_duplicate_groups": exact_duplicate_groups,
        "records": records,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
