"""AI-CCTV Sentinel — scripts/dataset/calculate_image_quality.py (Task 4 §26-29, pipeline step 7).

Computes and RECORDS blur (variance of Laplacian), brightness (mean
intensity), and contrast (intensity std-dev) per image. Does not
apply a universal hard-coded reject threshold — only flags images as
good/review/reject if thresholds are explicitly set in
configs/dataset.yaml (they default to null / disabled until validated
against real data, per Task 4 §27).

Usage:
    python scripts/dataset/calculate_image_quality.py [--root datasets/processed/annotated/images]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yaml  # noqa: E402
from annotation_schemas import ImageQualityMetrics, QualityFlag  # noqa: E402
from validate_files import SUPPORTED_IMAGE_EXTENSIONS, iter_candidate_files  # noqa: E402

DEFAULT_ROOT = Path("datasets/processed/annotated/images")
DATASET_CONFIG = Path("configs/dataset.yaml")
REPORT_PATH = Path("datasets/processed/image_quality_report.json")


def load_quality_config() -> dict:
    if not DATASET_CONFIG.exists():
        return {}
    data = yaml.safe_load(DATASET_CONFIG.read_text(encoding="utf-8")) or {}
    return data.get("quality", {})


def compute_metrics(path: Path) -> ImageQualityMetrics:
    metrics = ImageQualityMetrics(image_path=str(path))
    try:
        import cv2
        import numpy as np

        image = cv2.imread(str(path))
        if image is None:
            metrics.quality_flag = QualityFlag.REJECT
            metrics.notes.append("unreadable")
            return metrics

        height, width = image.shape[:2]
        metrics.width = width
        metrics.height = height
        metrics.aspect_ratio = round(width / height, 4) if height else None

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        metrics.blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        metrics.brightness_score = float(np.mean(gray))
        metrics.contrast_score = float(np.std(gray))
    except Exception as exc:  # noqa: BLE001
        metrics.quality_flag = QualityFlag.REJECT
        metrics.notes.append(f"error: {exc}")

    return metrics


def apply_flags(metrics: ImageQualityMetrics, config: dict) -> None:
    """Only flags 'review' if a threshold is actually configured
    (not null). Never invents a universal threshold (Task 4 §27)."""

    if metrics.quality_flag == QualityFlag.REJECT:
        return  # already rejected (unreadable)

    blur_threshold = config.get("blur_review_below")
    if config.get("enable_blur_check") and blur_threshold is not None and metrics.blur_score is not None:
        if metrics.blur_score < blur_threshold:
            metrics.quality_flag = QualityFlag.REVIEW
            metrics.notes.append(f"blur_score {metrics.blur_score:.1f} below configured threshold {blur_threshold}")

    low = config.get("brightness_low_below")
    high = config.get("brightness_high_above")
    if config.get("enable_brightness_check") and metrics.brightness_score is not None:
        if low is not None and metrics.brightness_score < low:
            metrics.quality_flag = QualityFlag.REVIEW
            metrics.notes.append("brightness below configured low threshold")
        if high is not None and metrics.brightness_score > high:
            metrics.quality_flag = QualityFlag.REVIEW
            metrics.notes.append("brightness above configured high threshold")


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate per-image quality metrics (Task 4).")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()

    config = load_quality_config()
    files = iter_candidate_files(args.root)
    image_files = [f for f in files if f.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS]

    results: list[ImageQualityMetrics] = []
    for path in image_files:
        metrics = compute_metrics(path)
        apply_flags(metrics, config)
        results.append(metrics)

    by_flag = {flag.value: len([r for r in results if r.quality_flag == flag]) for flag in QualityFlag}

    print("=" * 60)
    print("AI-CCTV Sentinel — Image Quality Metrics (Task 4, step 7)")
    print("=" * 60)
    print(f"Root scanned : {args.root}")
    print(f"Images       : {len(results)}")
    for flag, count in by_flag.items():
        print(f"  {flag:<8}: {count}")
    print("=" * 60)

    if not image_files:
        print(
            "No images found yet. No universal blur/brightness/contrast "
            "thresholds are hard-coded — see configs/dataset.yaml "
            "`quality.*_below` fields, which stay null until validated "
            "against real data (Task 4 §27)."
        )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "root": str(args.root),
                "config_used": config,
                "counts_by_flag": by_flag,
                "results": [r.model_dump(mode="json") for r in results],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
