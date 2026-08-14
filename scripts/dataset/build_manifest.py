"""AI-CCTV Sentinel — scripts/dataset/build_manifest.py (Task 3 §13).

Builds/refreshes datasets/metadata/dataset_manifest.json from
individual per-source JSON records under datasets/metadata/sources/.
This script never invents a source — it only aggregates whatever
source records a human has actually placed in
datasets/metadata/sources/*.json (see
datasets/metadata/sources/SOURCE_TEMPLATE.json for the required shape).

Usage:
    python scripts/dataset/build_manifest.py
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schemas import DatasetSource  # noqa: E402

SOURCES_DIR = Path("datasets/metadata/sources")
MANIFEST_PATH = Path("datasets/metadata/dataset_manifest.json")
DATASET_VERSION = "0.1.0"


def load_sources() -> list[DatasetSource]:
    sources: list[DatasetSource] = []
    if not SOURCES_DIR.exists():
        return sources

    for path in sorted(SOURCES_DIR.glob("*.json")):
        if path.name == "SOURCE_TEMPLATE.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            sources.append(DatasetSource(**data))
        except Exception as exc:  # noqa: BLE001
            print(f"WARNING: skipped invalid source file {path.name}: {exc}")
    return sources


def main() -> None:
    sources = load_sources()

    manifest = {
        "project": "AI-CCTV Sentinel",
        "dataset_version": DATASET_VERSION,
        "generated_at": date.today().isoformat(),
        "primary_classes": ["snake", "monkey", "dog", "person"],
        "optional_extension_classes": ["cattle", "wild_boar", "other_large_animal"],
        "snake_hierarchy": {"snake": ["likely_venomous", "likely_non_venomous", "unknown"]},
        "source_count": len(sources),
        "sources": [s.model_dump(mode="json") for s in sources],
    }

    print("=" * 60)
    print("AI-CCTV Sentinel — Dataset Manifest Builder")
    print("=" * 60)
    print(f"Source records found : {len(sources)}")
    if not sources:
        print(
            "PENDING: no source records exist yet under "
            f"{SOURCES_DIR}. Add one JSON file per dataset source "
            "(see SOURCE_TEMPLATE.json) and re-run this script."
        )
    print("=" * 60)

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Manifest written to: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
