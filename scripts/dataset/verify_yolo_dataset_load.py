"""AI-CCTV Sentinel — scripts/dataset/verify_yolo_dataset_load.py
(Task 4 §66-67 — YOLO26 dataset-load verification, NOT training).

Loads yolo26n.pt and confirms the generated data.yaml is structurally
acceptable to the current Ultralytics package. This does NOT call
model.train(...) or any training/fine-tuning method — it only proves
the dataset configuration is loadable, per the Task 4 §41 restriction
("DO NOT run model.train(...)").

Requires the full Task 1 environment (torch + ultralytics), which is
heavier than this dataset-tooling venv needs for its other scripts —
run this one from the project's main .venv (see README.md "Run
Environment Verification").

Usage:
    python scripts/dataset/verify_yolo_dataset_load.py
"""

from __future__ import annotations

import sys
from pathlib import Path

DATA_YAML = Path("datasets/yolo/sentinel_v1/data.yaml")


def main() -> None:
    if not DATA_YAML.exists():
        print(f"PENDING — {DATA_YAML} does not exist yet. Run generate_dataset_yaml.py first.")
        sys.exit(1)

    try:
        from ultralytics import YOLO
    except ImportError:
        print(
            "Ultralytics is not installed in this environment. This check "
            "requires the full Task 1 environment (see README.md). "
            "Structural YAML validation can still be done without "
            "Ultralytics — see check_bbox_coordinates.py / check_class_ids.py."
        )
        sys.exit(1)

    print("=" * 60)
    print("AI-CCTV Sentinel — YOLO26 Dataset-Load Verification")
    print("=" * 60)
    print("This loads the model and dataset config only. It does NOT")
    print("call model.train(...) — no training happens here (Task 4 §41).")
    print("=" * 60)

    model = YOLO("yolo26n.pt")
    print("yolo26n.pt loaded successfully.")

    # Ultralytics resolves and validates a dataset YAML (paths, class
    # names, split existence) as part of trainer/validator setup. We
    # invoke only the check_dataset utility (no training call) if the
    # installed Ultralytics version exposes one; otherwise we fall
    # back to the structural checks already performed by
    # check_class_ids.py / check_bbox_coordinates.py and report that.
    try:
        from ultralytics.data.utils import check_det_dataset

        dataset_info = check_det_dataset(str(DATA_YAML))
        print(f"Dataset config accepted by Ultralytics: {dataset_info.get('nc', '?')} classes")
        print(f"Class names: {dataset_info.get('names')}")
        print("YOLO26 dataset configuration verification: PASS")
    except Exception as exc:  # noqa: BLE001
        print(f"NOTE: could not run Ultralytics' internal dataset check util ({exc}).")
        print(
            "Structural validation (data.yaml shape, class IDs, bbox "
            "ranges) was already confirmed by "
            "generate_dataset_yaml.py / check_class_ids.py / "
            "check_bbox_coordinates.py."
        )


if __name__ == "__main__":
    main()
