# Data Quality Policy

**Status: CURRENT policy, implemented in `scripts/dataset/*.py` and verified against synthetic test data.**

## Image validation

Every image is checked for: readability (not corrupt), supported extension, non-zero size, valid width/height, valid channel count. An extension is never trusted as proof of validity — every file is actually opened and decoded (`validate_images.py`).

## Annotation validation

Every YOLO label line is checked for: correct field count (5), all-numeric values, class ID present in `configs/classes.yaml`, `x_center`/`y_center` in `[0,1]`, `width`/`height` in `(0,1]`, and the resulting box staying within image bounds (`validate_yolo_labels.py`, `check_class_ids.py`, `check_bbox_coordinates.py`). Invalid labels are only ever **reported**, never silently auto-corrected (Task 4 §19).

## Image/label pairing

Every image is checked against its expected label file and vice versa (`check_image_label_pairs.py`). A negative/hard-negative image legitimately having no label file is **not** an issue under the project's documented `empty_label_policy` (`configs/dataset.yaml`); an orphan label (a `.txt` with no matching image) **is** flagged as invalid.

## Duplicate detection

- **Exact duplicates** (SHA-256 match): flagged, and — only when the script is explicitly run with `--apply` (never by default) — moved to `datasets/quarantine/duplicates/`. Dry-run is the default mode (`detect_duplicates.py`).
- **Near duplicates** (perceptual-hash Hamming distance ≤ configurable threshold): flagged for **human review only**; never auto-removed, since a near-duplicate might be a legitimately different moment worth keeping.

## Image quality metrics

Blur (variance of Laplacian), brightness (mean pixel intensity), and contrast (pixel intensity std-dev) are computed and **recorded** for every image (`calculate_image_quality.py`). No universal hard-coded reject threshold is applied — `configs/dataset.yaml` → `quality.*_below` fields default to `null` (disabled) and only get real values once validated against actual collected data (Task 4 §27-29). Low-light and low-contrast images are explicitly **not** auto-rejected, since they represent real CCTV deployment conditions this project needs to handle.

## Corruption handling

Unreadable images are flagged `reject` with a `notes` entry explaining why (e.g. `"unreadable"` or the underlying decode error) — never silently dropped from the count.

## License / provenance

Every sample traces back to a `DatasetSource` record (Task 3's `scripts/dataset/schemas.py`) with its license, redistribution rights, and region. A sample from an incompatible or unclear license is not combined into the final dataset until reviewed (`datasets/quarantine/license_review/`).

## Quarantine, not deletion

Nothing is ever permanently deleted by any script in this pipeline. Rejected files move to a labeled subdirectory of `datasets/quarantine/`:

```text
datasets/quarantine/
├── corrupt/
├── duplicates/
├── invalid_annotations/
├── license_review/
└── quality_review/
```

Quarantined data is excluded from `build_yolo_dataset.py`'s output by construction (only files reachable via a valid group→split assignment are copied), and is never trained on.

## Human review

Automated checks are the first pass, not the final word. Any sample an automated check can't confidently classify (occlusion too heavy, ambiguous object, borderline quality score) routes to human review rather than a forced automatic decision, particularly for the review-priority categories in `docs/research/annotation-guidelines.md`.

## Quality gate — what must pass before a sample proceeds

```text
Readable + allowed source + known provenance + usable visual quality + correct high-level class
    → PASS → included in sentinel_v1 build
    → FAIL → quarantine/review, excluded from the build
```
