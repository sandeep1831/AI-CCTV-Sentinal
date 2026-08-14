"""AI-CCTV Sentinel — scripts/dataset/detect_duplicates.py (Task 4 §30, §55-57, pipeline step 6).

Detects exact duplicates (SHA-256) and near-duplicates (perceptual
hash) among annotated images. Supports --dry-run (default: True must
be explicitly overridden with --apply) so nothing moves unless
explicitly requested. When applying, exact duplicates are moved
(never deleted) to datasets/quarantine/duplicates/; near-duplicates
are only reported for human review, never auto-moved (Task 4 §30).

Usage:
    python scripts/dataset/detect_duplicates.py --root datasets/processed/annotated/images
    python scripts/dataset/detect_duplicates.py --root ... --apply
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from calculate_hashes import average_hash, sha256_of  # noqa: E402
from validate_files import SUPPORTED_IMAGE_EXTENSIONS, iter_candidate_files  # noqa: E402

DEFAULT_ROOT = Path("datasets/processed/annotated/images")
QUARANTINE_DUPLICATES_DIR = Path("datasets/quarantine/duplicates")
REPORT_PATH = Path("datasets/processed/duplicates_report.json")


def hamming_distance(hex_a: str, hex_b: str) -> int:
    int_a, int_b = int(hex_a, 16), int(hex_b, 16)
    return bin(int_a ^ int_b).count("1")


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect exact/near duplicates (Task 4).")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument(
        "--near-duplicate-threshold",
        type=int,
        default=5,
        help="Max Hamming distance between perceptual hashes to flag as a near-duplicate pair.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually move exact duplicates to quarantine. Without this flag, the script only reports (dry-run).",
    )
    args = parser.parse_args()

    files = iter_candidate_files(args.root)
    image_files = [f for f in files if f.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS]

    sha_groups: dict[str, list[Path]] = defaultdict(list)
    phashes: dict[Path, str | None] = {}

    for path in image_files:
        sha_groups[sha256_of(path)].append(path)
        phashes[path] = average_hash(path)

    exact_duplicate_groups = {h: paths for h, paths in sha_groups.items() if len(paths) > 1}
    files_to_quarantine: list[Path] = []
    for paths in exact_duplicate_groups.values():
        # Keep the first (by name), quarantine the rest.
        files_to_quarantine.extend(sorted(paths)[1:])

    near_duplicate_pairs: list[tuple[str, str, int]] = []
    hashed = [(p, h) for p, h in phashes.items() if h is not None]
    for i in range(len(hashed)):
        for j in range(i + 1, len(hashed)):
            path_a, hash_a = hashed[i]
            path_b, hash_b = hashed[j]
            distance = hamming_distance(hash_a, hash_b)
            if distance <= args.near_duplicate_threshold:
                near_duplicate_pairs.append((str(path_a), str(path_b), distance))

    print("=" * 60)
    print("AI-CCTV Sentinel — Duplicate Detection (Task 4, step 6)")
    print(f"Mode: {'APPLY (files will be moved)' if args.apply else 'DRY-RUN (no changes made)'}")
    print("=" * 60)
    print(f"Root scanned              : {args.root}")
    print(f"Images scanned            : {len(image_files)}")
    print(f"Exact-duplicate groups    : {len(exact_duplicate_groups)}")
    print(f"Files that would be moved : {len(files_to_quarantine)}")
    print(f"Near-duplicate pairs (<= {args.near_duplicate_threshold} bits): {len(near_duplicate_pairs)} (flagged for review only)")
    print("=" * 60)

    moved: list[dict] = []
    if args.apply and files_to_quarantine:
        QUARANTINE_DUPLICATES_DIR.mkdir(parents=True, exist_ok=True)
        for path in files_to_quarantine:
            destination = QUARANTINE_DUPLICATES_DIR / path.name
            counter = 1
            while destination.exists():
                destination = QUARANTINE_DUPLICATES_DIR / f"{path.stem}_{counter}{path.suffix}"
                counter += 1
            shutil.move(str(path), str(destination))
            moved.append({"from": str(path), "to": str(destination)})
        print(f"Moved {len(moved)} exact-duplicate file(s) to {QUARANTINE_DUPLICATES_DIR}")
    elif files_to_quarantine:
        print("Dry-run: no files were moved. Re-run with --apply to quarantine exact duplicates.")

    if not image_files:
        print("No images found yet — nothing to check for duplicates.")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "root": str(args.root),
                "applied": args.apply,
                "images_scanned": len(image_files),
                "exact_duplicate_groups": {h: [str(p) for p in paths] for h, paths in exact_duplicate_groups.items()},
                "files_quarantined": moved,
                "near_duplicate_pairs": near_duplicate_pairs,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
