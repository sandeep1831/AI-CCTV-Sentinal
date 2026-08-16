# Task 5 — Research Questions & Hypotheses

**Status: documented, unanswered.** These questions/hypotheses are written before any training has occurred (dataset v1.0.0 currently has 0 real samples — see `docs/research/dataset-v1-report.md`). They will be answered/tested only once real experiments produce real measured results, and this document will be updated with links to the actual `reports/experiments/EXP-*.md` that answer each one — never filled in speculatively.

## Research questions

**RQ1 — Can YOLO26n detect the selected campus-animal classes using our curated dataset?**
Answered by: EXP-001 baseline training + validation/test metrics (`reports/validation/EXP-001/`, `reports/test/EXP-001/`).

**RQ2 — Which class has the weakest detection performance?**
Answered by: the per-class metrics table in `reports/model-v1-report.md` §7, once real per-class precision/recall/F1/mAP exist.

**RQ3 — How does hard-negative data affect false positives?**
Answered by: EXP-004 (baseline dataset vs. hard-negative-enhanced dataset), contingent on Task 3 actually collecting sufficient hard negatives first (currently 0 — see `docs/research/dataset-gap-analysis.md`).

**RQ4 — How does CCTV-like data affect domain generalization?**
Answered by: comparing normal-test vs. domain-shift-test performance (Task 5 §45), contingent on `datasets/yolo/sentinel_v1_domain_shift/` actually being populated (currently empty).

**RQ5 — What confidence threshold provides a useful precision/recall trade-off?**
Answered by: `scripts/training/threshold_analysis.py` sweep results, `reports/threshold_analysis.md`.

**RQ6 — Does a larger YOLO26 model provide enough improvement to justify additional inference cost?**
Answered by: EXP-002 (YOLO26n vs. YOLO26s), comparing `reports/model_selection.md`'s accuracy/latency/resource trade-off analysis.

## Hypotheses (not conclusions)

**H1 — A pretrained YOLO26 detector can be adapted to the project dataset.**
Testable once EXP-001 actually runs to completion.

**H2 — Hard negatives can reduce false positives.**
Testable via EXP-004, once sufficient hard-negative data exists.

**H3 — CCTV-like training data can improve performance on deployment-like test data.**
Testable via the domain-relevance experiment (Task 5 §60), once sufficient CCTV-like data exists.

**H4 — A larger YOLO26 model may improve detection performance but increase latency/resource usage.**
Testable via EXP-002.

## Why none of these are answered yet

Per Task 5 §5: training does not start until `scripts/training/preflight_check.py` reports **READY**. As of this document, it reports:

```text
Train dataset : FAIL (images/train contains 0 images)
OVERALL: NOT READY
```

No training has occurred, so no question above can be honestly answered yet. See the project's final Task 5 status report for the explicit blocker and what's required to unblock it.
