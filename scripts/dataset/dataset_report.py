"""AI-CCTV Sentinel — scripts/dataset/dataset_report.py (Task 3 §41).

Aggregates real statistics from:
    - datasets/metadata/samples/*.json   (per-sample SampleMetadata records)
    - datasets/metadata/dataset_manifest.json (source registry)
    - datasets/metadata/validation_report.json (if present, from validate_files.py)
    - datasets/metadata/hashes.json            (if present, from calculate_hashes.py)

Never invents numbers. If no sample metadata exists yet, every count
is reported as 0 and the report says so explicitly, per Task 3 §41 /
§51 ("report the actual number of collected samples... explicitly
report PENDING").

Usage:
    python scripts/dataset/dataset_report.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schemas import SampleMetadata  # noqa: E402

SAMPLES_DIR = Path("datasets/metadata/samples")
MANIFEST_PATH = Path("datasets/metadata/dataset_manifest.json")
VALIDATION_REPORT_PATH = Path("datasets/metadata/validation_report.json")
HASHES_REPORT_PATH = Path("datasets/metadata/hashes.json")


def load_samples() -> list[SampleMetadata]:
    samples: list[SampleMetadata] = []
    if not SAMPLES_DIR.exists():
        return samples
    for path in sorted(SAMPLES_DIR.glob("*.json")):
        if path.name == "SAMPLE_TEMPLATE.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            samples.append(SampleMetadata(**data))
        except Exception as exc:  # noqa: BLE001
            print(f"WARNING: skipped invalid sample file {path.name}: {exc}")
    return samples


def load_json_if_exists(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def main() -> None:
    samples = load_samples()
    manifest = load_json_if_exists(MANIFEST_PATH) or {}
    validation = load_json_if_exists(VALIDATION_REPORT_PATH)
    hashes = load_json_if_exists(HASHES_REPORT_PATH)

    by_class = Counter(s.animal_class for s in samples)
    by_region = Counter(s.region for s in samples)
    by_lighting = Counter(s.lighting for s in samples)
    by_weather = Counter(s.weather for s in samples)
    by_media_type = Counter(s.media_type for s in samples)
    by_dataset = Counter(s.dataset_id for s in samples)

    print("=" * 60)
    print("AI-CCTV SENTINEL DATASET REPORT")
    print("=" * 60)
    print()
    print(f"Total samples recorded : {len(samples)}")
    print(f"Registered sources     : {manifest.get('source_count', 0)}")
    print()

    print("By class:")
    if by_class:
        for cls, count in sorted(by_class.items()):
            print(f"  {cls:<20}: {count}")
    else:
        print("  PENDING — no sample metadata recorded yet")
    print()

    print("By source dataset:")
    if by_dataset:
        for ds_id, count in sorted(by_dataset.items()):
            print(f"  {ds_id:<20}: {count}")
    else:
        print("  PENDING")
    print()

    print("By region:")
    if by_region:
        for region, count in sorted(by_region.items()):
            print(f"  {region:<20}: {count}")
    else:
        print("  PENDING")
    print()

    print("By lighting condition:")
    if by_lighting:
        for lighting, count in sorted(by_lighting.items()):
            print(f"  {lighting:<20}: {count}")
    else:
        print("  PENDING")
    print()

    print("By weather condition:")
    if by_weather:
        for weather, count in sorted(by_weather.items()):
            print(f"  {weather:<20}: {count}")
    else:
        print("  PENDING")
    print()

    print("By media type:")
    if by_media_type:
        for media_type, count in sorted(by_media_type.items()):
            print(f"  {media_type:<20}: {count}")
    else:
        print("  PENDING")
    print()

    print("File validation (scripts/dataset/validate_files.py):")
    if validation:
        print(f"  Valid files    : {validation.get('valid_files', 0)}")
        print(f"  Invalid files  : {validation.get('invalid_files', 0)}")
        print(f"  Duplicate names: {validation.get('duplicate_filenames', 0)}")
    else:
        print("  PENDING — run scripts/dataset/validate_files.py first")
    print()

    print("Hash / duplicate check (scripts/dataset/calculate_hashes.py):")
    if hashes:
        print(f"  Files hashed          : {hashes.get('file_count', 0)}")
        print(f"  Exact-duplicate groups: {len(hashes.get('exact_duplicate_groups', {}))}")
    else:
        print("  PENDING — run scripts/dataset/calculate_hashes.py first")

    print("=" * 60)

    if not samples:
        print(
            "No sample-level metadata exists yet. This report reflects the "
            "TOOLING, not a populated dataset — see "
            "docs/research/dataset-gap-analysis.md for current status and "
            "docs/research/dataset-strategy.md for the acquisition plan."
        )
        print("=" * 60)


if __name__ == "__main__":
    main()
