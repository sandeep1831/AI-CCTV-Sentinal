# Dataset Gap Analysis

**Status as of dataset v0.1.0.** Per Task 3 §45, a gap is only reported here once actual dataset inspection confirms it — not assumed. As of this writing, `scripts/dataset/inspect_dataset.py` and `scripts/dataset/dataset_report.py` both report **zero files and zero sample records** across every category. That single fact is the actual, confirmed state of the dataset, and it is the primary gap: **collection has not yet started.**

This document will be re-run and updated (not overwritten — see versioning policy) once real sources are onboarded, at which point per-dimension gaps (e.g. "few night images") can be stated as *confirmed by inspection* rather than assumed.

## Research data matrix (collection checklist, Task 3 §46)

| Dimension | Target | Current status |
|---|---|---|
| Snake | Primary | PENDING — 0 samples |
| Monkey | Primary | PENDING — 0 samples |
| Dog | Primary | PENDING — 0 samples |
| Person | Supporting | PENDING — 0 samples |
| CCTV viewpoint | Required | PENDING — 0 sources onboarded |
| Low resolution | Required | PENDING — not yet assessable |
| Low light | Required | PENDING — `raw/environment/low_light/` empty |
| Rain/wet | Important | PENDING — `raw/environment/rain/` empty |
| Occlusion | Required | PENDING — not yet assessable |
| Hard negatives | Required | PENDING — `raw/hard_negatives/` empty |
| Regional relevance | Important | PENDING — no source has established Telangana/AP provenance yet |
| Public data | Required | PENDING — 0 `DatasetSource` records in `datasets/metadata/sources/` |
| Human feedback | Future | Not applicable yet — no deployment exists |
| Domain-shift data | Required | PENDING — depends on primary collection existing first |

## How this will be re-assessed

Once at least one real source is onboarded (a filled-in `DatasetSource` record plus files under the matching `datasets/raw/<category>/` subdirectory):

1. Run `python scripts/dataset/validate_files.py --root datasets/raw` to confirm file-level quality.
2. Run `python scripts/dataset/calculate_hashes.py --root datasets/raw` to check for duplicates.
3. Run `python scripts/dataset/build_manifest.py` to refresh the manifest from source records.
4. Populate `datasets/metadata/samples/*.json` for collected files (or a bulk-import script built in a later task).
5. Run `python scripts/dataset/dataset_report.py` to get real per-class/region/lighting/weather counts.
6. Update this document's matrix with **confirmed** gaps (e.g. "snake: 40 samples, 0 of which are night-time" is a confirmed gap; "probably not enough night data" without inspection is not).

## Known structural constraints (not data gaps, but worth recording)

- No pilot campus CCTV access currently exists, which blocks the most valuable category (`cctv_like/`) until either a licensed CCTV-like public dataset is found or institutional permission for a real deployment is secured (see `docs/architecture/security-architecture.md` for the permission/authorization posture this project requires).
- Live-snake or other live-dangerous-animal collection on an occupied campus is explicitly disallowed (Task 3 §2) — snake data must come from public datasets, wildlife/forest-department sources, camera-trap archives, or non-living staged decoys.
- Regional (Telangana-specific) labeling requires provenance the team does not yet have for any source; until a source explicitly documents its collection location, all samples default to `region: Unknown`, not an assumed region.

## Explicit non-claims

This document does **not** claim:

- That any specific gap (e.g. "too few night images") has been measured, since no images exist to measure.
- That any dataset source has been vetted, licensed, or downloaded.
- Any dataset size, class balance, or diversity statistic — all such statistics are `PENDING`.
