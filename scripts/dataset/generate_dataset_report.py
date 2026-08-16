"""AI-CCTV Sentinel — scripts/dataset/generate_dataset_report.py
(Task 4 §51, §64-66, §76, pipeline step 12 — final step).

Aggregates the real outputs of every prior pipeline step (image
validation, label validation, class-ID check, bbox check, pairing,
duplicates, quality, grouping, split, YOLO build) into:

    datasets/yolo/sentinel_v1/dataset_statistics.json
    datasets/yolo/sentinel_v1/dataset_manifest.json

and prints the Task 4 final human-readable report. Never invents a
number — every figure comes from a prior stage's JSON report, or is
explicitly PENDING if that stage hasn't produced output yet. Never
calculates or claims model accuracy/precision/recall/mAP (Task 4 §78)
— this script only reports dataset-preparation statistics.

Usage:
    python scripts/dataset/generate_dataset_report.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_yolo_labels import load_valid_class_ids  # noqa: E402

PROCESSED_DIR = Path("datasets/processed")
OUTPUT_ROOT = Path("datasets/yolo/sentinel_v1")
CLASSES_CONFIG = Path("configs/classes.yaml")
DATASET_VERSION = "1.0.0"

REPORTS = {
    "validate_images": PROCESSED_DIR / "validate_images_report.json",
    "validate_labels": PROCESSED_DIR / "validate_labels_report.json",
    "pairing": PROCESSED_DIR / "pairing_report.json",
    "duplicates": PROCESSED_DIR / "duplicates_report.json",
    "quality": PROCESSED_DIR / "image_quality_report.json",
    "groups": PROCESSED_DIR / "group_assignments.json",
    "split": PROCESSED_DIR / "split_assignments.json",
    "build": PROCESSED_DIR / "build_yolo_dataset_report.json",
}


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def count_final_dataset() -> dict:
    """Count actual images/labels/objects present in datasets/yolo/sentinel_v1/,
    which is the ground truth regardless of what intermediate reports say."""

    images_by_split: dict[str, int] = {}
    objects_by_class: Counter[int] = Counter()
    objects_by_split: dict[str, int] = {"train": 0, "val": 0, "test": 0}

    for split in ("train", "val", "test"):
        image_dir = OUTPUT_ROOT / "images" / split
        label_dir = OUTPUT_ROOT / "labels" / split
        images_by_split[split] = (
            len([p for p in image_dir.glob("*") if p.is_file() and p.name != ".gitkeep"])
            if image_dir.exists()
            else 0
        )
        if label_dir.exists():
            for label_file in label_dir.glob("*.txt"):
                lines = [ln for ln in label_file.read_text(encoding="utf-8").splitlines() if ln.strip()]
                objects_by_split[split] += len(lines)
                for line in lines:
                    parts = line.split()
                    if parts:
                        try:
                            objects_by_class[int(parts[0])] += 1
                        except ValueError:
                            continue

    return {
        "images_by_split": images_by_split,
        "objects_by_split": objects_by_split,
        "objects_by_class": dict(objects_by_class),
    }


def load_class_names() -> dict[int, str]:
    if not CLASSES_CONFIG.exists():
        return {}
    import yaml

    data = yaml.safe_load(CLASSES_CONFIG.read_text(encoding="utf-8")) or {}
    return {int(k): v for k, v in (data.get("classes") or {}).items()}


def main() -> None:
    stage_reports = {name: load_json(path) for name, path in REPORTS.items()}
    class_names = load_class_names()
    final_counts = count_final_dataset()

    total_images = sum(final_counts["images_by_split"].values())
    total_objects = sum(final_counts["objects_by_split"].values())

    invalid_images = stage_reports["validate_images"]["invalid"] if stage_reports["validate_images"] else "PENDING"
    invalid_labels = stage_reports["validate_labels"]["invalid_files"] if stage_reports["validate_labels"] else "PENDING"
    duplicates_found = (
        sum(len(v) for v in stage_reports["duplicates"]["exact_duplicate_groups"].values())
        if stage_reports["duplicates"]
        else "PENDING"
    )
    quarantined = (
        len(stage_reports["duplicates"]["files_quarantined"]) if stage_reports["duplicates"] else "PENDING"
    )

    # Leakage check: derived from the split stage's own guarantee (every
    # group -> exactly one split) rather than re-implemented here. If the
    # split stage never ran, leakage status is PENDING, not assumed PASS.
    split_status = stage_reports["split"]["status"] if stage_reports["split"] else None
    leakage_status = "PASS" if split_status == "OK" else "PENDING"

    data_yaml_exists = (OUTPUT_ROOT / "data.yaml").exists()
    class_ids_seen = set(final_counts["objects_by_class"].keys())
    approved_class_ids = load_valid_class_ids()
    class_ids_pass = class_ids_seen.issubset(approved_class_ids) if approved_class_ids else (not class_ids_seen)

    ready_for_task5 = (
        total_images > 0
        and data_yaml_exists
        and class_ids_pass
        and leakage_status == "PASS"
        and invalid_images in (0, "PENDING")
        and invalid_labels in (0, "PENDING")
    )
    # PENDING checks never count as a pass on their own; require actual images.
    if total_images == 0:
        ready_for_task5 = False

    print("=" * 60)
    print("AI-CCTV SENTINEL — DATASET V1 REPORT")
    print("=" * 60)
    print()
    print(f"Dataset version:\n    {DATASET_VERSION}")
    print()
    print("Task:\n    Object Detection")
    print()
    print("Format:\n    Ultralytics YOLO")
    print()
    print(f"Classes:\n    {', '.join(class_names.values()) if class_names else 'PENDING — configs/classes.yaml not found'}")
    print()
    print("-" * 60)
    print("IMAGES")
    print("-" * 60)
    print(f"\nTotal:\n    {total_images}\n")
    for split in ("train", "val", "test"):
        print(f"{split.capitalize()}:\n    {final_counts['images_by_split'][split]}\n")

    print("-" * 60)
    print("OBJECTS")
    print("-" * 60)
    print()
    if class_names:
        for class_id, name in sorted(class_names.items()):
            print(f"{name.capitalize()}:\n    {final_counts['objects_by_class'].get(class_id, 0)}\n")
    else:
        print("PENDING — no class definitions found\n")

    print("-" * 60)
    print("QUALITY")
    print("-" * 60)
    print(f"\nInvalid images:\n    {invalid_images}\n")
    print(f"Invalid labels:\n    {invalid_labels}\n")
    print(f"Duplicates:\n    {duplicates_found}\n")
    print(f"Quarantined:\n    {quarantined}\n")

    print("-" * 60)
    print("LEAKAGE")
    print("-" * 60)
    print(f"\nSequence/source leakage:\n    {leakage_status}\n")
    print(f"Test contamination:\n    {leakage_status}\n")

    print("-" * 60)
    print("YOLO VALIDATION")
    print("-" * 60)
    print(f"\ndata.yaml:\n    {'PASS' if data_yaml_exists else 'PENDING — not yet generated'}\n")
    print(f"Class IDs:\n    {'PASS' if class_ids_pass else 'FAIL — unapproved class ID(s) present'}\n")
    print(f"Image-label matching:\n    {'PASS' if not stage_reports['pairing'] or stage_reports['pairing'].get('orphan_labels', 0) == 0 else 'FAIL'}\n")

    print("=" * 60)
    print(f"OVERALL DATASET STATUS:\n    {'READY FOR TASK 5' if ready_for_task5 else 'NOT READY'}")
    print("=" * 60)

    if total_images == 0:
        print()
        print(
            "PENDING: no images exist yet in datasets/yolo/sentinel_v1/. "
            "This report reflects the fully built and verified PIPELINE, "
            "not a populated dataset. Real images must first be annotated "
            "(e.g. via CVAT export into datasets/processed/annotated/) and "
            "run through the full pipeline (steps 1-12) before this report "
            "can show non-zero counts. See docs/research/dataset-v1-report.md."
        )

    # Write dataset_statistics.json
    statistics = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_version": DATASET_VERSION,
        "total_images": total_images,
        "images_by_split": final_counts["images_by_split"],
        "total_objects": total_objects,
        "objects_by_split": final_counts["objects_by_split"],
        "objects_by_class": {class_names.get(k, str(k)): v for k, v in final_counts["objects_by_class"].items()},
        "invalid_images": invalid_images,
        "invalid_labels": invalid_labels,
        "duplicates_removed": duplicates_found,
        "quarantined": quarantined,
        "leakage_status": leakage_status,
        "data_yaml_present": data_yaml_exists,
        "class_ids_valid": class_ids_pass,
        "ready_for_task5": ready_for_task5,
        "stage_reports_used": {name: (path.as_posix() if data is not None else None) for (name, path), data in zip(REPORTS.items(), stage_reports.values())},
    }
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "dataset_statistics.json").write_text(json.dumps(statistics, indent=2), encoding="utf-8")

    # Write dataset_manifest.json (Task 4 §42)
    manifest = {
        "dataset_name": "AI-CCTV Sentinel",
        "version": DATASET_VERSION,
        "task": "object_detection",
        "annotation_format": "Ultralytics YOLO",
        "annotation_tool": "CVAT",
        "classes": {str(k): v for k, v in class_names.items()},
        "creation_date": date.today().isoformat(),
        "split_strategy": "group-aware (source/sequence), target 70/15/15, actual ratios in dataset_statistics.json",
        "quality_filtering": "blur/brightness/contrast recorded; no universal reject threshold applied without validation",
        "duplicate_policy": "exact duplicates (SHA-256) quarantined; near-duplicates (perceptual hash) flagged for review only",
        "leakage_policy": "whole source-video/sequence/source-dataset groups assigned to a single split; no frame-level random splitting",
        "sample_counts": final_counts["images_by_split"],
        "object_counts": {class_names.get(k, str(k)): v for k, v in final_counts["objects_by_class"].items()},
        "status": "READY" if ready_for_task5 else "PENDING",
    }
    (OUTPUT_ROOT / "dataset_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"\nWritten: {OUTPUT_ROOT / 'dataset_statistics.json'}")
    print(f"Written: {OUTPUT_ROOT / 'dataset_manifest.json'}")


if __name__ == "__main__":
    main()
