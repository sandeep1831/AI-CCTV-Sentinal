# Specialist Safety-Sensitive Error Report

**Status: PENDING.** No specialist classifier has been trained for either branch.

## Snake: likely_venomous → likely_non_venomous

The single most dangerous possible classifier error. Will be reported here as an explicit count (not folded into overall accuracy) once `evaluate_snake_classifier.py` runs against a real trained model — see that script's current limitation note: it reports top-1/overall metrics only in this version, and the full pairwise confusion breakdown still needs to be added before this section can be filled in honestly.

## Dog: possible_wound / possible_injury → normal_visible_appearance

The dog-health equivalent of the dangerous-error case: a real abnormality mistaken for normal appearance. Will be reported here once DOG-HEALTH-EXP-001 has real data, a trained model, and a completed evaluation run.

## Why this document has no numbers yet

Per Task 6 §68 (inherited safety principle from Task 5): no fabricated results. Both branches are blocked on real data — see `docs/research/task6-research-questions.md` for the full blocker explanation.
