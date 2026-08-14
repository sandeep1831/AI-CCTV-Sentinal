# Dataset Strategy

**Status: CURRENT (strategy + tooling defined). Data collection itself is PENDING** — no images, videos, or frames have been collected yet. This document is the plan and the schema that collection will follow, per Task 3.

## 1. Dataset objective

Build a clean, traceable, representative, research-quality dataset for real-time multi-animal hazard detection on educational-campus CCTV, prioritizing **domain relevance over raw size**: CCTV-like viewpoint, low resolution, varied lighting/weather, occlusion, and background clutter matter more than a large collection of clean internet photographs (Task 3 §3, §48).

## 2. Target classes

**Primary:** `snake`, `monkey`, `dog`, `person`
**Optional extension** (only if quality data is available without compromising the primary scope): `cattle`, `wild_boar`, `other_large_animal`

This project is a hazard-detection system, not a comprehensive wildlife taxonomy — the class list intentionally stays small.

## 3. Snake classification hierarchy

```text
snake
├── likely_venomous
├── likely_non_venomous
└── unknown
```

Species-level identification (e.g. the medically important Indian "big four" — Indian cobra, common krait, Russell's viper, saw-scaled viper) is a **stretch goal**, not a Task 3/60-day requirement, and uncertain visual species classification must never be treated as definitive. The venomous/non-venomous distinction is the minimum useful classification task, per the reference paper.

## 4. Source categories

| Category | Directory | Purpose |
|---|---|---|
| Public datasets | `datasets/raw/public/` | General pretraining/classification base (e.g. SnakeCLEF-style, other licensed CV datasets) |
| Regional data | `datasets/raw/regional/` | Telangana/Andhra Pradesh/India-specific footage where provenance genuinely supports the label |
| CCTV-like data | `datasets/raw/cctv_like/` | Elevated/wide-angle/low-resolution footage resembling actual deployment conditions |
| Staged (non-living) | `datasets/raw/staged/` | Controlled, non-dangerous staged footage (decoys, props) — never live dangerous animals |
| Hard negatives | `datasets/raw/hard_negatives/` | Rope, hose, wire, cable, stick, shadow, and other detector-confusing objects |
| Feedback | `datasets/raw/feedback/{confirmed,false_positive,uncertain}/` | Future human-confirmed samples from live deployment (Task 2's self-learning architecture) |
| Environmental subsets | `datasets/raw/environment/{low_light,rain}/` | Explicit low-light and monsoon-condition subsets |

## 5. Public dataset strategy

Only onboard a dataset after recording its full `DatasetSource` metadata (`scripts/dataset/schemas.py`) — name, source URL, publisher, license, commercial-use/redistribution/research-use/attribution flags, class list, counts, region, and download date. A dataset is never downloaded merely because it's large; it must plausibly serve the primary classes and, ideally, resemble deployment conditions (Task 3 §6, §48).

## 6. Regional data strategy

An image may only be labeled with `region: Telangana` (or any specific region) if the source **actually establishes** that location — never inferred or assumed for convenience (Task 3 §9). Where provenance doesn't establish location, `region` is `Unknown`.

## 7. CCTV-like data strategy

Prioritized characteristics: elevated/fixed camera mount, wide-angle view, low resolution, long-distance/small-object animals, partial occlusion, background clutter. If a pilot campus becomes available, only authorized camera feeds are used, with formal institutional permission, minimizing incidental recording of identifiable people and never capturing live dangerous-animal footage (Task 3 §8). Until then, this category relies on legally licensed CCTV-like datasets, wildlife camera-trap footage, and controlled staged/synthetic data.

## 8. Hard negatives

A dedicated, first-class category (not an afterthought), directly motivated by the reference paper's observation that single-stage detectors can misfire on ropes, hoses, cables, and shadows. Target objects: rope, hose, wire, cable, stick, branch, leaf, shadow, plastic pipe, curved object, animal-like object, blurred object (Task 3 §19). Background-only images (empty corridor, classroom, playground, etc.) are collected alongside these to evaluate false positives (Task 3 §20).

## 9. Environmental diversity

Metadata fields (`Lighting`, `Weather`, `TimeOfDay` enums in `scripts/dataset/schemas.py`) are recorded per sample, never fabricated. Explicit subsets are planned for low-light/night conditions and monsoon/rain conditions, since the reference paper identifies both as directly relevant to the campus snake-incursion problem (Task 3 §22-23). No claim of night-time model performance will be made until actually tested.

## 10. Data quality

Every candidate file passes through the quality gate defined in `scripts/dataset/validate_files.py`: readable, correct extension, non-zero size, acceptable dimensions, no duplicate filename collision. Results are `good`, `acceptable`, or `unusable` — unusable files are quarantined (moved, never deleted) for human review, never silently discarded (Task 3 §16, §39, §47).

## 11. Duplicate detection

`scripts/dataset/calculate_hashes.py` computes SHA-256 for exact-duplicate detection and a lightweight average-hash for image near-duplicate flagging. Exact duplicates must not appear in more than one train/validation/test split once splitting happens in Task 4 (Task 3 §17).

### Video/sequence leakage (critical)

Correlated frames from the same source video must stay together in a single split — entire videos are assigned to train, validation, or test, never individual frames randomly distributed across splits. This is documented here as a hard requirement for Task 4 to enforce; Task 3 does not extract frames or create splits (Task 3 §18, §32).

## 12. Dataset versioning

Versions follow semantic-ish tags (`0.1.0`, `0.2.0`, ...). Each version's manifest snapshot lives in `datasets/versions/v<version>.json` and is never overwritten; `datasets/versions/CHANGELOG.md` records only changes that actually happened (Task 3 §30-31). Current version: **v0.1.0** — directory scaffold and tooling only, 0 samples.

## 13. Privacy

Any data containing identifiable people requires verified institutional/legal permission, minimized retention, documented source, and consideration of anonymization. Private CCTV footage is never uploaded to a public repository (Task 3 §42).

## 14. Licensing / publication policy

Redistribution rights are checked before any dataset is published alongside the research paper. If redistribution isn't permitted, only statistics, methodology, and schema are published — not raw images (Task 3 §43). See `datasets/metadata/licenses/README.md`.

## 15. Train/validation/test strategy (planning only — not executed in Task 3)

Candidate split: **70% train / 15% validation / 15% test**, applied source-aware, video-aware, sequence-aware, and class-aware to avoid leakage. The test set, once created in Task 4, is held out completely — never used for training, active-learning selection, tuning, retraining, or threshold optimization (Task 3 §32-33).

## 16. Domain-shift evaluation (future)

A separate CCTV-like test subset, deliberately drawn from different lighting/angle/background/resolution/location than the main training distribution, is planned to evaluate adaptation later (Task 3 §34).

## 17. Future feedback dataset

`datasets/raw/feedback/{confirmed,false_positive,uncertain}/` exists as an empty, real structure today — it will receive genuine human-confirmed samples once the system is deployed (Task 2's human-in-the-loop architecture), never fabricated placeholder data (Task 3 §35).

## 18. Limitations

- **No data has been collected yet.** Every count in this project's manifest and reports is 0 as of v0.1.0.
- No pilot campus CCTV access currently exists; CCTV-like data depends on finding appropriately licensed third-party sources or producing controlled staged/synthetic footage.
- Perceptual-hash near-duplicate detection here is a lightweight average-hash, not a full-featured library — adequate for flagging likely near-duplicates for human review, not a certified dedup guarantee.
- Regional (Telangana-specific) data availability is unknown until actual sourcing is attempted — see `docs/research/dataset-gap-analysis.md`.
