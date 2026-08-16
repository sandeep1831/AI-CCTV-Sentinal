# Model v1 Report

**Status: BLOCKED / PENDING.** No training has occurred. `scripts/training/preflight_check.py` reports `NOT READY` (0 images in `datasets/yolo/sentinel_v1/images/train/`). This document is the required report structure, populated with real values only once EXP-001 actually completes — see the Task 5 final status report for the exact blocker.

## 1. Model

Planned: YOLO26n (`yolo26n.pt`), pretrained weights fine-tuned on Sentinel v1. Not yet trained.

## 2. Dataset

`datasets/yolo/sentinel_v1/` (dataset version 1.0.0). Currently 0 images, 0 objects across all splits — see `docs/research/dataset-v1-report.md`.

## 3. Training configuration

Defined in `configs/training/baseline.yaml` (EXP-001): 100 epochs (patience 20), image size 640, batch auto, device auto, seed 42. Not yet executed.

## 4. Hardware

Will be recorded automatically in `runs/experiments/EXP-001/environment.json` by `train_baseline.py` at actual training time, from whichever machine actually runs it. Not yet recorded.

## 5. Validation results

PENDING — `reports/validation/EXP-001/validation_metrics.json` does not exist yet.

## 6. Test results

PENDING — `reports/test/EXP-001/test_metrics.json` does not exist yet. Per policy, this must only be generated once, after model/threshold decisions are frozen using train/val data only.

## 7. Per-class results

PENDING.

| Class | Precision | Recall | F1 | mAP50 | mAP50-95 |
|---|---|---|---|---|---|
| snake | — | — | — | — | — |
| monkey | — | — | — | — | — |
| dog | — | — | — | — | — |
| person | — | — | — | — | — |

## 8. Snake analysis

PENDING — see `reports/snake_detection_analysis.md` (also a PENDING placeholder).

## 9. False-positive analysis

PENDING — see `reports/false_positive_analysis.md`.

## 10. False-negative analysis

PENDING — no evaluation has run.

## 11. Threshold analysis

PENDING — `scripts/training/threshold_analysis.py` has not been run (requires a trained model).

## 12. Speed analysis

PENDING — `scripts/training/benchmark_model.py` has not been run.

## 13. Domain-shift analysis

PENDING — `datasets/yolo/sentinel_v1_domain_shift/` is currently empty (Task 4 gap); even once a model exists, this analysis is only meaningful once that subset is populated.

## 14. Model selection

PENDING — see `reports/model_selection.md`. No model comparison is possible with zero trained candidates.

## 15. Limitations

The primary limitation blocking Task 5 entirely: **the Task 4 dataset contains 0 annotated images.** No amount of training configuration or evaluation tooling can substitute for real data. Every other limitation this project might report (class imbalance, small-object performance, domain shift, etc.) is downstream of this one and cannot yet be assessed.

## 16. Next task

Task 6 (Animal Classification) explicitly depends on a completed Task 5 candidate model. Per Task 5 §98, Task 6 must not begin until `best.pt` + real metrics + reports + model metadata + dataset version are all verified — none of which exist yet. Task 6 remains blocked on the same root cause as Task 5: real annotated data.
