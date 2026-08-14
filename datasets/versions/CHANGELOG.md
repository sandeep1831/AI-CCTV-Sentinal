# Dataset Changelog

## v0.1.0 — Task 3 (current)

- Initial dataset directory structure created (`raw/{public,regional,cctv_like,staged,feedback,hard_negatives}`,
  `metadata/{sources,samples,licenses}`, `processed/`, `annotations/`, `versions/`).
- Initial class definitions: primary = `snake, monkey, dog, person`; optional extension = `cattle, wild_boar, other_large_animal`.
- Initial snake hierarchy defined: `likely_venomous / likely_non_venomous / unknown`.
- Initial provenance schema defined (`scripts/dataset/schemas.py`: `DatasetSource`, `SampleMetadata`).
- Initial empty dataset manifest created (`datasets/metadata/dataset_manifest.json`) — **0 sources registered**.
- Dataset tooling created: `inspect_dataset.py`, `validate_files.py`, `calculate_hashes.py`,
  `build_manifest.py`, `dataset_report.py`.
- No image, video, or frame data has been collected yet. All counts are 0. See
  `docs/research/dataset-gap-analysis.md` for what is PENDING.

## v1.0.0 — Task 4 (current, scaffold)

- Created the full YOLO-compatible dataset structure: `datasets/yolo/sentinel_v1/{images,labels}/{train,val,test}/`,
  plus an optional `datasets/yolo/sentinel_v1_domain_shift/` subset.
- Created `datasets/quarantine/{corrupt,duplicates,invalid_annotations,license_review,quality_review}/`.
- Added `configs/classes.yaml` (authoritative class-ID mapping: snake, monkey, dog, person)
  and `configs/dataset.yaml` (split targets, quality/duplicate/leakage policy).
- Built and verified the complete 12-step annotation/preprocessing/splitting pipeline
  (`scripts/dataset/validate_images.py` → `generate_dataset_report.py`), including
  group-aware, leakage-free train/val/test splitting.
- Verified the full pipeline end-to-end against synthetic test data (two simulated
  video sequences) — confirmed sequences are never split across train/val/test —
  then removed the synthetic data before finalizing this version.
- Generated `datasets/yolo/sentinel_v1/data.yaml` (Ultralytics YOLO dataset config,
  relative paths, 4 classes) and structurally validated it against the Ultralytics
  YOLO dataset-YAML convention.
- **No real images have been annotated or added yet.** All counts in
  `dataset_statistics.json` and `dataset_manifest.json` are 0. Dataset status:
  **NOT READY** for Task 5 until real annotated data exists. See
  `docs/research/dataset-v1-report.md`.

<!--
Future entries — only add a new version section here once real changes
have actually been made (Task 3 §30-31: "do not overwrite previous
manifests" / "only record changes that actually happened").

## v1.0.1
- ...
-->
