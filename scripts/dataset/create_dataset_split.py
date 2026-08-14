"""AI-CCTV Sentinel — scripts/dataset/create_dataset_split.py (Task 4 §31-34, pipeline step 9).

Assigns each GROUP (from create_group_ids.py — never individual
images) to train, val, or test. This guarantees no correlated frames
from the same source video/sequence/dataset ever span multiple
splits. Targets the percentages in configs/dataset.yaml `split.*` but
reports the ACTUAL achieved split rather than forcing exact
percentages at the expense of leakage prevention (Task 4 §33).

Assignment is deterministic given a fixed random seed, so re-running
this script on the same group set reproduces the same split.

Usage:
    python scripts/dataset/create_dataset_split.py
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yaml  # noqa: E402
from annotation_schemas import SplitAssignment, SplitName  # noqa: E402

GROUPS_REPORT = Path("datasets/processed/group_assignments.json")
DATASET_CONFIG = Path("configs/dataset.yaml")
REPORT_PATH = Path("datasets/processed/split_assignments.json")
DEFAULT_SEED = 42


def load_split_targets() -> dict[str, float]:
    if not DATASET_CONFIG.exists():
        return {"train": 0.70, "val": 0.15, "test": 0.15}
    data = yaml.safe_load(DATASET_CONFIG.read_text(encoding="utf-8")) or {}
    return data.get("split", {"train": 0.70, "val": 0.15, "test": 0.15})


def load_groups() -> dict[str, int]:
    """Return {group_id: file_count} from create_group_ids.py's output."""

    if not GROUPS_REPORT.exists():
        return {}
    data = json.loads(GROUPS_REPORT.read_text(encoding="utf-8"))
    counts: dict[str, int] = {}
    for assignment in data.get("assignments", []):
        counts[assignment["group_id"]] = counts.get(assignment["group_id"], 0) + 1
    return counts


def greedy_group_split(group_counts: dict[str, int], targets: dict[str, float], seed: int) -> dict[str, str]:
    """Assign whole groups to splits using a greedy largest-first
    bin-packing approach against the target file-count ratios. This
    keeps every group intact (no leakage) while tracking as closely as
    practical to the configured train/val/test targets."""

    total_files = sum(group_counts.values())
    if total_files == 0:
        return {}

    target_counts = {name: total_files * ratio for name, ratio in targets.items()}
    current_counts = {name: 0.0 for name in targets}

    rng = random.Random(seed)
    # Sort groups largest-first for stable, leakage-safe bin packing;
    # shuffle within equal sizes for reproducible but non-alphabetic tie-breaking.
    items = list(group_counts.items())
    rng.shuffle(items)
    items.sort(key=lambda kv: kv[1], reverse=True)

    assignment: dict[str, str] = {}
    for group_id, count in items:
        # Assign to whichever split is currently furthest below its target.
        deficits = {name: target_counts[name] - current_counts[name] for name in targets}
        best_split = max(deficits, key=lambda name: deficits[name])
        assignment[group_id] = best_split
        current_counts[best_split] += count

    return assignment


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a group-aware train/val/test split (Task 4).")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    targets = load_split_targets()
    group_counts = load_groups()

    if not group_counts:
        print("=" * 60)
        print("AI-CCTV Sentinel — Dataset Split (Task 4, step 9)")
        print("=" * 60)
        print(
            "PENDING — no groups found. Run create_group_ids.py first "
            f"(expected report at {GROUPS_REPORT})."
        )
        print("=" * 60)
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(
            json.dumps(
                {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "status": "PENDING",
                    "reason": "no groups available",
                    "targets": targets,
                    "assignments": [],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return

    group_to_split = greedy_group_split(group_counts, targets, args.seed)

    split_file_counts = {"train": 0, "val": 0, "test": 0}
    assignments: list[SplitAssignment] = []
    for group_id, split_name in group_to_split.items():
        count = group_counts[group_id]
        split_file_counts[split_name] += count
        assignments.append(SplitAssignment(group_id=group_id, split=SplitName(split_name), file_count=count))

    total_files = sum(split_file_counts.values())
    actual_ratios = {name: (count / total_files if total_files else 0.0) for name, count in split_file_counts.items()}

    print("=" * 60)
    print("AI-CCTV Sentinel — Dataset Split (Task 4, step 9)")
    print("=" * 60)
    print(f"Groups            : {len(group_counts)}")
    print(f"Total files        : {total_files}")
    print(f"Target split       : {targets}")
    print(f"Actual split (files): train={split_file_counts['train']} "
          f"({actual_ratios['train']:.1%}), val={split_file_counts['val']} "
          f"({actual_ratios['val']:.1%}), test={split_file_counts['test']} "
          f"({actual_ratios['test']:.1%})")
    print("Leakage guarantee  : every group assigned to exactly one split")
    print("=" * 60)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "status": "OK",
                "seed": args.seed,
                "targets": targets,
                "actual_ratios": actual_ratios,
                "split_file_counts": split_file_counts,
                "group_count": len(group_counts),
                "assignments": [a.model_dump(mode="json") for a in assignments],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
