# Self-Learning Architecture

**Status: FUTURE.** This entire document describes interfaces and data flow only — Task 2 explicitly excludes any active-learning algorithm, drift algorithm, training implementation, or automatic deployment logic (Task 2 §47).

## Why this exists

The uploaded reference paper proposes using dismissed alerts as hard-negative examples for periodic retraining. This architecture generalizes that idea into a **controlled model lifecycle**, so the system can improve from real campus data over time without ever silently degrading in production.

## Data flow

See [`docs/diagrams/05-self-learning-lifecycle.mermaid`](../diagrams/05-self-learning-lifecycle.mermaid).

```text
Detection → Human Feedback → Verified Sample → Sample Selection →
Dataset Version → Training Run → Candidate Model → Evaluation → Deployment Decision
```

## Components (all interfaces only — `ai/learning/interfaces.py`)

### SampleSelectionEngine (active learning)

Selects which detections/feedback pairs are worth a human's time to review for a future dataset. Candidate criteria (Task 2 §24), none of which are scored or weighted yet:

- low confidence
- high uncertainty
- false positive (per human feedback)
- new environment
- new camera
- underrepresented class

### DriftMonitor

Watches for changes in confidence distribution, class distribution, image quality, false-positive rate, environmental variation, and camera characteristics. Produces a `DriftReport` with a `drift_score` against a `threshold`.

**Critical design rule:** drift detection never triggers retraining automatically.

```text
Drift detected → Sample collection → Human validation → Retraining decision
```

### TrainingManager

Launches and tracks training runs (`TrainingRun`), given a `dataset_version` and `base_model_version`. No training logic exists yet.

### ModelRegistry

The safety-critical component. States: `TRAINING → VALIDATING → CANDIDATE → STAGED → PRODUCTION`, with `REJECTED` and `ARCHIVED` as terminal/side states. See [`docs/diagrams/06-model-lifecycle.mermaid`](../diagrams/06-model-lifecycle.mermaid).

**Critical design rule:** a new model is never automatically promoted to `PRODUCTION` merely because it finished training. Promotion requires an explicit, evaluated decision (`ModelRegistry.promote()`), and a worse-performing candidate is rejected (`ModelRegistry.reject()`) while the existing production model is left untouched. `ModelRegistry.rollback()` exists specifically so a bad promotion can be reversed.

## Human-in-the-loop is the gate, not a suggestion

Every stage that could affect what ends up in production — sample selection, drift-triggered review, and model promotion — is designed to require human validation, not fully automatic action. This is intentional: an early-warning system around potentially dangerous animals must not silently retrain itself into worse behavior.
