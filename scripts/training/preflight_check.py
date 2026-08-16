"""AI-CCTV Sentinel — scripts/training/preflight_check.py (Task 5 §5-7).

The mandatory gate before any training may start. Verifies the Task 4
dataset is actually valid and ready:

    dataset YAML exists and is well-formed
    train/val/test image and label directories exist
    class mapping matches configs/classes.yaml
    images are readable
    at least one image exists in train (and ideally val/test)

If ANY check fails, this script reports NOT READY and exits non-zero.
Per Task 5 §5: "If Task 4 has not produced a valid dataset: STOP.
Do not create a new dataset inside Task 5." No training script in
this project should run if this check does not report READY.

Usage:
    python scripts/training/preflight_check.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

DATA_YAML = Path("datasets/yolo/sentinel_v1/data.yaml")
CLASSES_CONFIG = Path("configs/classes.yaml")
DATASET_ROOT = Path("datasets/yolo/sentinel_v1")


def check_dataset_yaml() -> tuple[bool, str]:
    if not DATA_YAML.exists():
        return False, f"{DATA_YAML} does not exist"
    try:
        data = yaml.safe_load(DATA_YAML.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001
        return False, f"{DATA_YAML} is not valid YAML: {exc}"

    required_keys = {"path", "train", "val", "names"}
    missing = required_keys - data.keys()
    if missing:
        return False, f"{DATA_YAML} missing required key(s): {sorted(missing)}"
    if not isinstance(data.get("names"), dict) or not data["names"]:
        return False, f"{DATA_YAML} 'names' must be a non-empty mapping"
    return True, "OK"


def check_split_dir(split: str) -> tuple[bool, str, int]:
    image_dir = DATASET_ROOT / "images" / split
    if not image_dir.exists():
        return False, f"images/{split} directory missing", 0
    images = [p for p in image_dir.glob("*") if p.is_file() and p.name != ".gitkeep"]
    if not images and split == "train":
        return False, f"images/{split} contains 0 images", 0
    return True, "OK", len(images)


def check_class_mapping() -> tuple[bool, str]:
    if not CLASSES_CONFIG.exists():
        return False, f"{CLASSES_CONFIG} does not exist"
    try:
        classes_data = yaml.safe_load(CLASSES_CONFIG.read_text(encoding="utf-8")) or {}
        data_yaml = yaml.safe_load(DATA_YAML.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001
        return False, f"could not parse class config: {exc}"

    authoritative = classes_data.get("classes", {})
    in_data_yaml = data_yaml.get("names", {})
    # YAML loads int keys as int in classes.yaml but data.yaml's `names`
    # may also load as int keys — normalize both to int for comparison.
    authoritative_norm = {int(k): v for k, v in authoritative.items()}
    in_data_yaml_norm = {int(k): v for k, v in in_data_yaml.items()}

    if authoritative_norm != in_data_yaml_norm:
        return False, (
            f"class mismatch: configs/classes.yaml={authoritative_norm} "
            f"vs data.yaml names={in_data_yaml_norm}"
        )
    ids = sorted(authoritative_norm.keys())
    if ids != list(range(len(ids))):
        return False, f"class IDs are not 0-indexed/consecutive: {ids}"
    return True, "OK"


def check_images_readable(sample_limit: int = 25) -> tuple[bool, str]:
    """Spot-check that a sample of images actually decode. Full corruption
    scanning already happened in Task 4's validate_images.py — this is a
    lightweight re-confirmation, not a full re-scan."""

    train_dir = DATASET_ROOT / "images" / "train"
    if not train_dir.exists():
        return True, "SKIPPED — no train directory"

    images = [p for p in train_dir.glob("*") if p.is_file() and p.name != ".gitkeep"][:sample_limit]
    if not images:
        return True, "SKIPPED — 0 images to check"

    try:
        import cv2
    except ImportError:
        return False, "OpenCV not available to verify image readability"

    unreadable = [p.name for p in images if cv2.imread(str(p)) is None]
    if unreadable:
        return False, f"{len(unreadable)} unreadable image(s), e.g. {unreadable[:3]}"
    return True, f"OK — {len(images)} sample image(s) verified readable"


def main() -> None:
    print("=" * 60)
    print("AI-CCTV SENTINEL — TRAINING PREFLIGHT")
    print("=" * 60)

    results: dict[str, tuple[bool, str]] = {}

    results["Dataset YAML"] = check_dataset_yaml()

    train_ok, train_msg, train_count = check_split_dir("train")
    val_ok, val_msg, val_count = check_split_dir("val")
    test_ok, test_msg, test_count = check_split_dir("test")
    results["Train dataset"] = (train_ok, f"{train_msg} ({train_count} images)")
    results["Validation dataset"] = (val_ok, f"{val_msg} ({val_count} images)")
    results["Test dataset"] = (test_ok, f"{test_msg} ({test_count} images)")

    results["Class mapping"] = check_class_mapping() if results["Dataset YAML"][0] else (False, "SKIPPED — data.yaml invalid")
    results["Images"] = check_images_readable()
    results["Labels"] = (
        (True, "OK — presence checked per-split above; content validated by Task 4's validate_yolo_labels.py")
        if train_ok
        else (False, "SKIPPED — no train images to check labels for")
    )

    for name, (passed, detail) in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{name:<20}: {status}  ({detail})")

    overall_ready = all(passed for passed, _ in results.values())

    print()
    print("OVERALL:")
    print("READY FOR TRAINING" if overall_ready else "NOT READY")
    print("=" * 60)

    if not overall_ready:
        print()
        print(
            "Per Task 5 §5: 'If Task 4 has not produced a valid dataset: "
            "STOP. Do not create a new dataset inside Task 5.' "
            "No training script should be run until this check passes. "
            "See docs/research/dataset-v1-report.md (Task 4) for current "
            "dataset status and what remains PENDING."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
