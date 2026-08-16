# Task 6 — Research Questions & Hypotheses

**Status: documented, unanswered.** Both specialist branches currently have 0 training samples — `scripts/specialists/specialist_report.py` reports `NOT READY`. These questions will be answered only with real measured results from `reports/specialists/{snake,dog_health}/evaluation_*.md`, never speculatively.

## Research questions

**RQ1 — Can a specialist classifier distinguish likely venomous, likely non-venomous and unknown snake categories from detector-generated regions?**
Answered by: `evaluate_snake_classifier.py` top-1 accuracy + safety error matrix, once SNAKE-EXP-001 completes on real ground-truth-cropped data.

**RQ2 — How does specialist classification performance compare across different snake visibility conditions?**
Answered by: per-visibility-condition breakdown, contingent on the underlying Task 4 dataset actually carrying occlusion/lighting metadata for snake samples (currently 0 samples exist to carry any metadata).

**RQ3 — Can visible dog-health screening identify possible wounds or abnormalities from sufficiently visible dog images?**
Answered by: `evaluate_dog_health.py`, contingent on Task 6 §52's data-sufficiency gate being satisfied first (currently 0 staged samples in `datasets/specialists/dog_health/_incoming/`).

**RQ4 — How strongly does body visibility affect dog-health screening performance?**
Answered by: comparing performance across `full_body_visible` / `partial_body_visible` / `insufficient_visibility` subsets, once real data exists in each.

**RQ5 — Does specialist analysis improve the usefulness of the initial animal detector for risk-aware campus monitoring?**
Answered by: a downstream integration comparison (detector-only vs. detector+specialist) that depends on Task 5's detector actually being trained first (also currently blocked — see Task 5's status report).

## Hypotheses (not conclusions)

**H1 — A specialist classifier will provide more useful snake-category information than the generic detector alone.**
Untested — no specialist classifier has been trained.

**H2 — The `unknown` class will reduce unsafe overconfident snake classification.**
Untested. The `unknown_threshold` in `configs/specialists/snake.yaml` is currently a placeholder (0.60) explicitly not yet validated against real data (Task 6 §18).

**H3 — Dog-health screening performance will decrease when body visibility is poor.**
Untested — no dog-health classifier has been trained; the visibility-override policy (§31) is implemented and unit-tested in `specialist_inference.py`, but its effect on measured performance is unverified.

**H4 — A visibility-aware screening system will produce fewer inappropriate health alerts than a classifier that always predicts a health class.**
Untested. This would require an ablation comparing with/without the visibility gate on real data.

## Why none of these are answered yet

Both specialist branches inherit the same root blocker as Task 5: the Task 4 dataset (and any staged dog-health data) contains 0 real samples. `scripts/specialists/create_snake_crops.py` correctly produces 0 crops from 0 ground-truth snake boxes; `scripts/specialists/create_dog_health_dataset.py` correctly reports PENDING with 0 staged files. Both training scripts (`train_snake_classifier.py`, `train_dog_health_classifier.py`) refuse to run — verified directly — rather than training on fabricated or insufficient data.
