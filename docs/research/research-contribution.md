# Research Contribution

**Status: CURRENT (documentation).** This document frames the M.Tech contribution; it makes no experimental claims, since no experiments have been run yet.

## Framing the contribution

The uploaded reference paper already reviews prior YOLO/CNN-based snake and animal detection work, and establishes a baseline CCTV → RTSP → edge/server → detection → classification → temporal consistency → alert → human confirmation architecture. This project does **not** claim to be the first to apply AI to animal detection on camera. Its contribution is the **integrated adaptive architecture and an experimentally validated self-improvement pipeline** built around that baseline, specifically:

1. **Existing CCTV reuse** — no new camera hardware required; the system is designed to sit on top of infrastructure a campus already has.
2. **Edge-based inference** — detection runs locally, sending only metadata + event snapshots outward, rather than continuously streaming raw video to a backend/cloud.
3. **Multi-animal hazard detection** — a configurable class list (not hard-coded to snakes only) so the same architecture generalizes to other campus hazards (e.g. monkeys, stray dogs).
4. **Temporal false-alarm reduction** — a dedicated consistency layer (minimum frames + minimum duration) before any detection becomes an alert-worthy event, extending the paper's consecutive-frame confirmation idea into a configurable, swappable component.
5. **Risk-aware alerting** — a zone-aware, configurable risk-scoring engine (not just "detected/not detected"), so the same animal class can produce different urgency depending on where and how persistently it was seen.
6. **Human-in-the-loop feedback** — every significant alert supports CONFIRM/DISMISS/UNCERTAIN, captured as structured, reusable metadata rather than free-text logs.
7. **Active learning** *(architecture only)* — a defined interface for selecting which feedback-backed samples are worth including in future training data, rather than retraining on everything indiscriminately.
8. **Data/model drift monitoring** *(architecture only)* — a defined interface for detecting distribution shift (confidence, class balance, image quality, environment, camera characteristics) that triggers human review rather than assuming any papers' latency/accuracy figures transfer unchanged to this deployment.
9. **Controlled model retraining** *(architecture only)* — training runs are tracked objects (`TrainingRun`), never an ad-hoc script run against production data.
10. **Model validation and rollback** *(architecture only)* — a model lifecycle registry (`TRAINING → VALIDATING → CANDIDATE → STAGED → PRODUCTION`, with `REJECTED`/`ARCHIVED`) that requires an explicit, evaluated decision before any promotion, and supports reverting a bad promotion.

Items 7-10 are explicitly **future work** in this project's timeline — Task 2 defines their interfaces and data contracts so that implementing them later does not require rearchitecting the system (Task 2 §50).

## Baseline vs. proposed system

### Baseline (reference paper)

```text
CCTV → YOLO → Alert
```

### Proposed (this project)

```text
CCTV
 → Edge inference
 → YOLO26
 → Tracking
 → Temporal verification
 → Classification
 → Risk assessment
 → Multi-channel alert
 → Human feedback
 → Active learning
 → Drift detection
 → Controlled retraining
 → Model evaluation
 → Deployment / rollback
```

The reference paper establishes the detect → classify → confirm baseline; this project's contribution is the surrounding adaptive architecture — temporal verification, zone-aware risk scoring, a typed event contract shared across every layer, and a safety-gated self-improvement loop.

## Experiment architecture (future — not run in Task 2)

Planned ablation studies, each adding one architectural layer on top of the last:

```text
Experiment A — YOLO26 only
Experiment B — YOLO26 + tracking
Experiment C — YOLO26 + tracking + temporal filtering
Experiment D — YOLO26 + tracking + temporal + risk
Experiment E — Full adaptive system
```

### Metrics to measure later

The reference paper identifies detection precision/recall/mAP, classification accuracy, false alarms, latency, and uptime as useful evaluation metrics. This project's `ModelMetrics` schema (`backend/schemas/model.py`) additionally tracks F1 and FPS, and will report:

```text
mAP, precision, recall, F1, false-positive rate, latency, FPS, GPU/CPU usage, adaptation improvement
```

No results are generated in Task 2 — these are the metrics the eventual experiments (A–E) will report against real, measured hardware, not assumed literature values (see `docs/architecture/deployment-architecture.md` § Latency budget).

## Safety framing

This system is an **AI-assisted early-warning system**. It is explicitly not a replacement for trained personnel, not a wildlife identification authority, not a medical decision system, and it never instructs anyone to approach a detected animal. For dangerous-animal events, the intended flow is:

```text
AI Alert → Authorized human → Appropriate trained response
```

consistent with the reference paper's recommendation of expert/forest-department verification before anyone approaches a detected snake.
