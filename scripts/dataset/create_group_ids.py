"""AI-CCTV Sentinel — scripts/dataset/create_group_ids.py (Task 4 §31-32, pipeline step 8).

Assigns every image a group_id so that correlated files (frames from
the same source video/sequence, or images from the same tightly
correlated source dataset) are later kept together in a single split
by create_dataset_split.py. This is the leakage-prevention mechanism
required before any splitting happens.

Grouping strategy (in priority order, matching configs/dataset.yaml
`leakage.*`):
    1. If sample metadata (datasets/metadata/samples/<sample_id>.json,
       from Task 3) records a source video/sequence, group by that.
    2. Otherwise group by dataset_id (source dataset) if known.
    3. Otherwise each file is its own singleton group (safe default —
       never assume unrelated files share a group).

Usage:
    python scripts/dataset/create_group_ids.py [--root datasets/processed/annotated/images]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from annotation_schemas import GroupAssignment  # noqa: E402
from schemas import SampleMetadata  # noqa: E402
from validate_files import SUPPORTED_IMAGE_EXTENSIONS, iter_candidate_files  # noqa: E402

DEFAULT_ROOT = Path("datasets/processed/annotated/images")
SAMPLES_DIR = Path("datasets/metadata/samples")
REPORT_PATH = Path("datasets/processed/group_assignments.json")

# Matches a common video-frame export naming convention:
# "<video_id>_frame_<n>.jpg" -> group by <video_id>. This is only a
# fallback heuristic for files with no sample metadata; it never
# fabricates a group for files that don't match, they simply become
# singletons instead.
FRAME_PATTERN = re.compile(r"^(?P<video_id>.+?)_frame_\d+$")


def load_sample_index() -> dict[str, SampleMetadata]:
    """Map original_filename (stem) -> SampleMetadata, if recorded."""

    index: dict[str, SampleMetadata] = {}
    if not SAMPLES_DIR.exists():
        return index
    for path in SAMPLES_DIR.glob("*.json"):
        if path.name == "SAMPLE_TEMPLATE.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            sample = SampleMetadata(**data)
            index[Path(sample.original_filename).stem] = sample
        except Exception:  # noqa: BLE001
            continue
    return index


def assign_group(path: Path, sample_index: dict[str, SampleMetadata]) -> GroupAssignment:
    stem = path.stem
    sample = sample_index.get(stem)

    if sample is not None:
        # Prefer explicit dataset_id grouping from recorded provenance
        # over filename heuristics.
        return GroupAssignment(
            path=str(path),
            group_id=f"source_dataset:{sample.dataset_id}",
            group_kind="source_dataset",
        )

    match = FRAME_PATTERN.match(stem)
    if match:
        return GroupAssignment(
            path=str(path),
            group_id=f"source_video_id:{match.group('video_id')}",
            group_kind="sequence",
        )

    return GroupAssignment(path=str(path), group_id=f"singleton:{stem}", group_kind="singleton")


def main() -> None:
    parser = argparse.ArgumentParser(description="Assign leakage-prevention group IDs (Task 4).")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()

    sample_index = load_sample_index()
    files = iter_candidate_files(args.root)
    image_files = [f for f in files if f.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS]

    assignments = [assign_group(p, sample_index) for p in image_files]

    by_kind: dict[str, int] = {}
    groups: dict[str, int] = {}
    for assignment in assignments:
        by_kind[assignment.group_kind] = by_kind.get(assignment.group_kind, 0) + 1
        groups[assignment.group_id] = groups.get(assignment.group_id, 0) + 1

    print("=" * 60)
    print("AI-CCTV Sentinel — Group ID Assignment (Task 4, step 8)")
    print("=" * 60)
    print(f"Root scanned      : {args.root}")
    print(f"Images            : {len(image_files)}")
    print(f"Distinct groups   : {len(groups)}")
    print(f"By group kind     : {by_kind}")
    print("=" * 60)

    if not image_files:
        print("No images found yet — nothing to group.")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "root": str(args.root),
                "image_count": len(image_files),
                "group_count": len(groups),
                "by_group_kind": by_kind,
                "assignments": [a.model_dump(mode="json") for a in assignments],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
