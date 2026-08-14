# AI-CCTV Sentinel

Self-Learning Edge-AI CCTV System for Real-Time Multi-Animal Hazard Detection and Risk-Aware Alerting in Educational Campuses.

## Current Status

Task 4 — Dataset Annotation, Preprocessing & Splitting

Tasks 1-3 are complete. Task 4 adds the full annotation validation,
preprocessing, leakage-free splitting, and YOLO26 dataset-build
pipeline. **The pipeline is built and verified (including against
synthetic test data), but no real images have been annotated yet** —
`datasets/yolo/sentinel_v1/` currently contains 0 samples. See
`docs/research/dataset-v1-report.md` for honest current status.

## Technology Direction

- Python
- PyTorch
- Ultralytics YOLO26
- OpenCV
- FastAPI
- Pydantic
- PostgreSQL (later task)
- Flutter (later task)
- MQTT/IoT (later task)

## Current Task

Environment setup and verification.

## Setup (Windows)

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip

# Install the current Stable PyTorch build for your machine from
# https://pytorch.org/get-started/locally/ (CPU or CUDA, as applicable)

python -m pip install -U ultralytics opencv-python numpy pandas matplotlib scikit-learn pillow pyyaml
python -m pip install -U fastapi "uvicorn[standard]" pydantic

python -m pip freeze > requirements.txt
```

## Run Environment Verification

```bash
python scripts/verify_environment.py
```

## Architecture (Task 2)

- `docs/architecture/` — system, data-flow, component, deployment,
  failure-handling, security/privacy, and self-learning architecture
- `docs/api/api-contracts.md` — backend API route/responsibility contracts
- `docs/research/research-contribution.md` — research framing, baseline vs.
  proposed comparison, experiment design
- `docs/diagrams/*.mermaid` — 9 architecture diagrams (render on GitHub or
  any Mermaid-compatible viewer)
- `configs/*.yaml` — camera, video, model, risk, alerts, system configuration
  templates (no secrets — see `.env.example`)
- `backend/schemas/` — typed data contracts (Camera, Detection, Track, Event,
  Alert, Feedback, ModelVersion, ...)
- `ai/*/interface*.py`, `backend/services/*.py`, `ai/learning/interfaces.py` —
  abstract interfaces for every pipeline component (Detector, Tracker,
  TemporalValidator, Classifier, RiskEngine, EventManager, AlertManager,
  FeedbackManager, SampleSelectionEngine, DriftMonitor, TrainingManager,
  ModelRegistry)

### Validate the configuration + schema foundation

```bash
python -c "from backend.core.config import load_app_config; print(load_app_config())"
```

## Dataset tooling (Task 3)

- `datasets/raw/{public,regional,cctv_like,staged,hard_negatives,environment,feedback}/` —
  raw source data by category (empty until real sources are onboarded)
- `datasets/metadata/{sources,samples,licenses}/` — provenance, per-sample
  metadata, and license records (see `*_TEMPLATE.json` files)
- `datasets/metadata/dataset_manifest.json` — aggregated source registry
- `datasets/versions/` — versioned manifest snapshots + `CHANGELOG.md`
- `scripts/dataset/schemas.py` — shared Pydantic schemas for sources/samples
- `scripts/dataset/inspect_dataset.py` — structural overview of `datasets/`
- `scripts/dataset/validate_files.py` — file-level quality gate (never deletes;
  use `--quarantine` to move invalid files for review)
- `scripts/dataset/calculate_hashes.py` — SHA-256 + perceptual hash for
  duplicate detection
- `scripts/dataset/build_manifest.py` — aggregates `datasets/metadata/sources/*.json`
  into the manifest
- `scripts/dataset/dataset_report.py` — real statistics from recorded metadata
  (reports `PENDING` honestly where no data exists yet)
- `docs/research/dataset-strategy.md` — full collection/curation strategy
- `docs/research/dataset-gap-analysis.md` — honest current-state gap analysis

```bash
python scripts/dataset/inspect_dataset.py
python scripts/dataset/validate_files.py --root datasets/raw
python scripts/dataset/calculate_hashes.py --root datasets/raw
python scripts/dataset/build_manifest.py
python scripts/dataset/dataset_report.py
```

## Annotation, preprocessing & splitting (Task 4)

- `configs/classes.yaml` — authoritative class-ID mapping (0=snake, 1=monkey, 2=dog, 3=person)
- `configs/dataset.yaml` — split targets, quality/duplicate/leakage policy
- `datasets/yolo/sentinel_v1/` — final YOLO-compatible dataset (`images/`, `labels/`
  per split, `data.yaml`, `dataset_manifest.json`, `dataset_statistics.json`)
- `datasets/yolo/sentinel_v1_domain_shift/` — optional domain-shift evaluation subset
- `datasets/quarantine/{corrupt,duplicates,invalid_annotations,license_review,quality_review}/` —
  rejected files (never deleted, only quarantined)
- `docs/research/annotation-guidelines.md` — the annotation standard (CVAT, class rules,
  hard negatives, snake/person special handling)
- `docs/research/dataset-splitting-policy.md` — leakage-free, group-aware splitting policy
- `docs/research/data-quality-policy.md` — validation, duplicate, and quality-gate policy
- `docs/research/dataset-v1-report.md` — current dataset status (honest — 0 samples so far)

The 12-step pipeline (run in order once real annotated data exists under
`datasets/processed/annotated/{images,labels}/`, e.g. exported from CVAT):

```bash
python scripts/dataset/validate_images.py
python scripts/dataset/validate_yolo_labels.py
python scripts/dataset/check_class_ids.py
python scripts/dataset/check_bbox_coordinates.py
python scripts/dataset/check_image_label_pairs.py
python scripts/dataset/detect_duplicates.py          # dry-run by default; add --apply to quarantine
python scripts/dataset/calculate_image_quality.py
python scripts/dataset/create_group_ids.py
python scripts/dataset/create_dataset_split.py
python scripts/dataset/build_yolo_dataset.py
python scripts/dataset/generate_dataset_yaml.py
python scripts/dataset/generate_dataset_report.py
```

Optional live Ultralytics dataset-load check (requires the full Task 1
environment — torch + ultralytics):

```bash
python scripts/dataset/verify_yolo_dataset_load.py
```

## Run Individual Checks

```bash
python scripts/test_pytorch.py
python scripts/test_yolo.py
python scripts/test_opencv.py
python scripts/test_inference.py
```

## Run FastAPI

```bash
uvicorn backend.main:app --reload
```

- API: http://127.0.0.1:8000
- API Documentation: http://127.0.0.1:8000/docs

## Project Structure

```
AI-CCTV-Sentinel/
├── ai/
│   ├── detection/        # Detector interface
│   ├── tracking/         # Tracker interface
│   ├── temporal/         # TemporalValidator interface
│   ├── classification/   # Classifier interface
│   ├── risk/             # RiskEngine interface
│   ├── learning/         # SampleSelectionEngine, DriftMonitor,
│   │                      # TrainingManager, ModelRegistry (future)
│   └── training/          # reserved for future training scripts
├── backend/
│   ├── api/               # endpoint implementations (deferred)
│   ├── core/              # config.py — settings + YAML loader
│   ├── database/          # reserved (PostgreSQL — future)
│   ├── models/             # reserved (ORM models — future)
│   ├── schemas/            # typed data contracts (Camera, Event, ...)
│   ├── services/            # VideoSource, EventManager, AlertManager,
│   │                         # FeedbackManager interfaces
│   ├── middleware/           # reserved (auth/logging — future)
│   └── main.py                # FastAPI app (Task 1)
├── configs/                    # camera/video/model/risk/alerts/system YAML
├── datasets/
│   ├── raw/                          # public/, regional/, cctv_like/, staged/,
│   │                                  # hard_negatives/, environment/, feedback/ (not committed*)
│   ├── metadata/                      # sources/, samples/, licenses/, dataset_manifest.json
│   ├── processed/                      # annotated/ staging area (CVAT export lands here; not committed)
│   ├── annotations/                     # reserved (legacy placeholder; annotations now live in
│   │                                     # datasets/processed/annotated/labels/ pre-build)
│   ├── yolo/
│   │   ├── sentinel_v1/                  # final YOLO dataset: images/, labels/ (train/val/test,
│   │   │                                  # not committed*), data.yaml, dataset_manifest.json,
│   │   │                                  # dataset_statistics.json (committed)
│   │   └── sentinel_v1_domain_shift/      # optional domain-shift evaluation subset
│   ├── quarantine/                        # corrupt/, duplicates/, invalid_annotations/,
│   │                                       # license_review/, quality_review/ (never auto-deleted)
│   └── versions/                           # CHANGELOG.md + versioned manifest snapshots
│   # *raw/, processed/, and yolo/*/images|labels are .gitignore'd for actual media;
│   # metadata/, versions/, and yolo/*/{data.yaml,*.json} ARE committed
├── models/                       # production/, candidates/, archive/ (not committed)
├── scripts/                       # environment + verification scripts
│   └── dataset/                    # dataset collection/curation tooling (Task 3)
├── tests/                          # test suite
├── docs/
│   ├── architecture/                # 7 architecture documents
│   ├── api/                          # API contracts
│   ├── research/                      # research contribution
│   └── diagrams/                       # 9 Mermaid diagrams
├── frontend/                            # future Flutter/web client
├── logs/                                 # runtime logs (not committed)
├── temp/                                  # scratch/output space (not committed)
├── app.py                                  # entry point
└── requirements.txt                          # reproducible dependency list
```
