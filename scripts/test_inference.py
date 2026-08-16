"""AI-CCTV Sentinel — Basic YOLO26 inference smoke test.

This does NOT set up the project dataset. It only proves the pipeline
Image -> YOLO26 -> Inference -> Detection result works end to end,
using the pretrained yolo26n.pt weights.

A small local sample image is generated on the fly (no external
network dependency), so this check also passes on offline or
firewalled machines. If a real test image is placed at
scripts/assets/test.jpg, that image is used instead.
"""

from pathlib import Path

import numpy as np
from ultralytics import YOLO


def get_sample_image() -> str:
    """Return a path to an image to run inference on.

    Prefers a user-provided scripts/assets/test.jpg. Falls back to a
    generated placeholder image so the check has no external
    dependencies.
    """
    custom_image = Path("scripts/assets/test.jpg")
    if custom_image.exists():
        return str(custom_image)

    generated_dir = Path("temp")
    generated_dir.mkdir(parents=True, exist_ok=True)
    generated_image = generated_dir / "sample_input.jpg"

    if not generated_image.exists():
        import cv2

        # Simple synthetic RGB image; only used to prove the
        # image -> YOLO26 -> inference pipeline runs end to end.
        rng = np.random.default_rng(seed=0)
        frame = rng.integers(0, 255, size=(480, 640, 3), dtype=np.uint8)
        cv2.imwrite(str(generated_image), frame)

    return str(generated_image)


def main() -> None:
    print("=" * 60)
    print("YOLO26 Basic Inference Check")
    print("=" * 60)

    model = YOLO("yolo26n.pt")
    source = get_sample_image()
    print(f"Using image      : {source}")

    results = model.predict(
        source=source,
        save=True,
        project="temp",
        name="inference_check",
        exist_ok=True,
    )

    for result in results:
        num_detections = len(result.boxes) if result.boxes is not None else 0
        print(f"Detections found : {num_detections}")

    output_dir = Path("temp") / "inference_check"
    print(f"Output saved to  : {output_dir.resolve()}")
    print("YOLO26 inference completed.")
    print("Inference check : PASSED")


if __name__ == "__main__":
    main()
