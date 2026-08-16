# Dataset Splitting Policy

**Status: CURRENT policy, implemented and verified in `scripts/dataset/create_group_ids.py` and `create_dataset_split.py`.**

## Target split

**70% train / 15% validation / 15% test** (`configs/dataset.yaml` → `split.*`) is the initial target — not a guarantee. If the actual, leakage-free grouping of the real data makes these exact percentages impractical, `create_dataset_split.py` reports the **actual achieved split** rather than forcing the targets at the expense of leakage prevention (Task 4 §33). This was demonstrated directly: a synthetic 12-file/4-group test run produced an 83/8/8 split, not 70/15/15, because with so few groups exact percentages aren't achievable — and the script correctly reported the real numbers rather than fudging them.

## Random frame-level splitting of correlated video frames is prohibited.

This is the central rule of this document. Given a source video:

```text
Video A
 ├── frame 001
 ├── frame 002
 ├── frame 003
 └── frame 004
```

**all frames must land in the same split.** Assigning `frame 001 → train, frame 002 → val, frame 003 → test` is data leakage: it lets the model implicitly "see" validation/test content during training (because adjacent frames are near-identical), which inflates apparent performance without representing genuine generalization.

## Grouping mechanism

`create_group_ids.py` assigns every image a `group_id` before any split decision is made, using this priority order:

1. **Recorded provenance** (`datasets/metadata/samples/<id>.json` from Task 3) — group by `dataset_id` if the sample's source dataset is known.
2. **Filename sequence heuristic** — a `<video_id>_frame_<n>` naming pattern groups by `video_id`.
3. **Singleton fallback** — if neither applies, the file is its own group. This is the safe default: the script never assumes two unrelated files share a group just to make grouping look cleaner.

`create_dataset_split.py` then assigns **whole groups** — never individual files — to train/val/test using a greedy, deterministic (seeded) bin-packing algorithm that tracks as close as practical to the configured target ratios while guaranteeing every group lands entirely in one split.

## Source-aware splitting

Beyond sequence-level grouping, images from the same tightly-correlated source dataset are also grouped, so a source that dominates the data can't silently leak near-duplicate content across train and test (Task 4 §32).

## Test-set protection

Once created, the **test split must never be used for**: training, augmentation selection, threshold tuning, hyperparameter tuning, active learning, or model selection. It exists solely as the final, held-out evaluation set (Task 4 §34). No script in this pipeline writes to the test split except `build_yolo_dataset.py`'s initial copy step.

## Domain-shift evaluation

A separate, optional subset — `datasets/yolo/sentinel_v1_domain_shift/` — is reserved for conditions that genuinely differ from the main training distribution (night, rain, a different camera/location/background/resolution). This is kept apart from the ordinary test set so mixing populations doesn't compromise either evaluation's interpretation (Task 4 §35). It is currently empty; see its `README.md` for status.

## Verification

The leakage guarantee was verified with a synthetic two-video test (6-frame and 4-frame sequences): both sequences landed entirely within a single split (`train`), never split across boundaries, confirming the grouping/splitting logic works as designed before being applied to any real data.
