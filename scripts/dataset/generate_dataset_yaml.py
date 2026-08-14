"""AI-CCTV Sentinel — scripts/dataset/generate_dataset_yaml.py (Task 4 §40, pipeline step 11).

Writes datasets/yolo/sentinel_v1/data.yaml from configs/classes.yaml,
using project-relative paths (never a machine-specific absolute path),
matching the Ultralytics YOLO dataset YAML convention: path, train,
val, optional test, and names.

Usage:
    python scripts/dataset/generate_dataset_yaml.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yaml  # noqa: E402

CLASSES_CONFIG = Path("configs/classes.yaml")
OUTPUT_ROOT = Path("datasets/yolo/sentinel_v1")
OUTPUT_YAML = OUTPUT_ROOT / "data.yaml"


def load_classes() -> dict[int, str]:
    if not CLASSES_CONFIG.exists():
        raise FileNotFoundError(f"{CLASSES_CONFIG} not found — cannot generate data.yaml without approved class list.")
    data = yaml.safe_load(CLASSES_CONFIG.read_text(encoding="utf-8")) or {}
    classes = data.get("classes") or {}
    return {int(k): v for k, v in classes.items()}


def main() -> None:
    classes = load_classes()

    dataset_yaml = {
        "path": ".",
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": classes,
    }

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    with OUTPUT_YAML.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(dataset_yaml, handle, sort_keys=False, default_flow_style=False)

    print("=" * 60)
    print("AI-CCTV Sentinel — Generate data.yaml (Task 4, step 11)")
    print("=" * 60)
    print(f"Classes : {classes}")
    print(f"Written : {OUTPUT_YAML}")
    print("=" * 60)
    print(
        "Note: paths are relative to this file's directory "
        f"({OUTPUT_ROOT}), per Ultralytics convention. No machine-specific "
        "absolute path is used."
    )


if __name__ == "__main__":
    main()
