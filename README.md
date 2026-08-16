# AI-CCTV Sentinel

Self-Learning Edge-AI CCTV System for Real-Time Multi-Animal Hazard Detection and Risk-Aware Alerting in Educational Campuses.

## Current Status

Task 6 — Specialist Animal Classification & Dog Visible-Health Screening

Tasks 1-5 are complete (Task 5 blocked on real data). Task 6 adds two
specialist branches — snake likely_venomous/likely_non_venomous/unknown
classification, and dog visible-health SCREENING (never diagnosis) —
both built and verified end-to-end, but **neither has real training
data**: `scripts/specialists/specialist_report.py` reports `NOT READY`.
See `docs/research/task6-research-questions.md`.

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

## Model training & evaluation (Task 5)

- `configs/training/{baseline,experiment,hardware}.yaml` — EXP-001 config,
  planned experiment matrix, hardware/device policy
- `scripts/training/preflight_check.py` — **mandatory gate**; run this first,
  every time, before any training
- `scripts/training/train_baseline.py` — main training entry point (refuses
  to run if preflight fails)
- `scripts/training/validate_model.py` / `evaluate_test.py` — real metrics
  from val/test splits (test set is protected — see `--force`/`--reason`)
- `scripts/training/threshold_analysis.py` — confidence threshold sweep (val only)
- `scripts/training/test_inference.py` — small-sample exploratory inference
- `scripts/training/benchmark_model.py` — PyTorch latency/FPS on actual hardware
- `scripts/training/compare_experiments.py` — reads real per-experiment metrics
- `scripts/training/save_experiment_metadata.py` — registers a model into
  `models/candidates/` with SHA-256 + dataset compatibility metadata
- `reports/model-v1-report.md`, `model_selection.md`, `threshold_analysis.md`,
  `false_positive_analysis.md`, `snake_detection_analysis.md` — all currently
  **PENDING placeholders**, populated only with real measured results
- `docs/research/task5-research-questions.md` — RQs/hypotheses, unanswered until real experiments run

**Current status: blocked.** Run the gate yourself to see why:

```bash
python scripts/training/preflight_check.py
```

```text
Train dataset : FAIL  (images/train contains 0 images)
OVERALL: NOT READY
```

Training will not start until this reports READY — see
`docs/research/dataset-v1-report.md` for what's needed to unblock it.
Once real annotated data exists and this gate passes:

```bash
python scripts/training/train_baseline.py
python scripts/training/validate_model.py --weights runs/detect/sentinel_yolo26n_baseline/weights/best.pt --experiment-id EXP-001
python scripts/training/threshold_analysis.py --weights <best.pt> --experiment-id EXP-001
python scripts/training/evaluate_test.py --weights <best.pt> --experiment-id EXP-001   # run once, protocol frozen
python scripts/training/benchmark_model.py --weights <best.pt> --experiment-id EXP-001
python scripts/training/save_experiment_metadata.py --weights <best.pt> --experiment-id EXP-001 --model-version v1.0.0
```

## Specialist analysis (Task 6)

Two independent branches, both **screening, never diagnosis** — every
result carries `diagnosis: false` and is enforced by a Pydantic
validator (`backend/schemas/specialist.py`) that rejects any attempt
to set it otherwise.

- `configs/specialists/{snake,dog_health}.yaml` — class definitions, crop/visibility policy, thresholds
- `schemas/specialist_result.schema.json` + `backend/schemas/specialist.py` — common output contract
- `scripts/specialists/create_snake_crops.py` — generates crops from Task 4 **ground-truth** boxes only
- `scripts/specialists/create_dog_health_dataset.py` — organizes staged, licensed, human-labeled dog images
  (stage them in `datasets/specialists/dog_health/_incoming/`, git-ignored)
- `scripts/specialists/train_snake_classifier.py` / `train_dog_health_classifier.py` — refuse to train
  below a minimum-samples-per-class threshold (never fabricate data)
- `scripts/specialists/evaluate_snake_classifier.py` / `evaluate_dog_health.py` — real metrics only
- `scripts/specialists/specialist_inference.py` — common `predict(animal=..., crop=...)` interface;
  returns `specialist_status="invalid"` gracefully if no model is registered yet
- `scripts/specialists/specialist_report.py` — the Task 6 status report

**Current status: blocked**, same root cause as Task 5:

```bash
python scripts/specialists/specialist_report.py
```

Both branches report `NOT READY` / `PENDING` — 0 training crops for
snake (needs Task 4 snake annotations), 0 staged samples for dog
health (needs licensed, human-labeled images in `_incoming/`). Once
real data exists:

```bash
python scripts/specialists/create_snake_crops.py
python scripts/specialists/train_snake_classifier.py
python scripts/specialists/evaluate_snake_classifier.py --weights <best.pt> --experiment-id SNAKE-EXP-001

python scripts/specialists/create_dog_health_dataset.py
python scripts/specialists/train_dog_health_classifier.py
python scripts/specialists/evaluate_dog_health.py --weights <best.pt> --experiment-id DOG-HEALTH-EXP-001
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
├── models/                       # production/, candidates/, archive/ (models not committed, metadata JSON is)
├── runs/
│   └── experiments/                # EXP-001/, EXP-002/, ... (environment.json, training_duration.json)
├── reports/
│   ├── experiments/                 # EXP-*.md write-ups
│   ├── validation/                   # per-experiment validation_metrics.json
│   ├── test/                          # per-experiment test_metrics.json (protected — run once)
│   ├── plots/                          # training curves, PR curve, class performance
│   ├── error_gallery/                   # false_positive/, false_negative/, low_confidence/,
│   │                                     # small_object/, occlusion/, low_light/
│   ├── model-v1-report.md, model_selection.md, threshold_analysis.md,
│   │   false_positive_analysis.md, snake_detection_analysis.md
├── scripts/                       # environment + verification scripts
│   ├── dataset/                    # dataset collection/curation/annotation tooling (Task 3+4)
│   └── training/                    # training/evaluation pipeline (Task 5)
├── tests/                          # test suite
├── docs/
│   ├── architecture/                # 7 architecture documents
│   ├── api/                          # API contracts
│   ├── research/                      # research contribution, dataset strategy,
│   │                                    # annotation guidelines, splitting/quality policy,
│   │                                    # dataset-v1-report, task5-research-questions
│   └── diagrams/                       # 9 Mermaid diagrams
├── frontend/                            # future Flutter/web client
├── logs/                                 # runtime logs (not committed)
├── temp/                                  # scratch/output space (not committed)
├── app.py                                  # entry point
└── requirements.txt                          # reproducible dependency list
```
