# Annotation Guidelines

**Status: CURRENT policy.** No annotation has been performed yet (0 annotated samples as of dataset v1.0.0 scaffold) — this document is the standard that will govern annotation once real images are staged for it.

## Annotation tool

**CVAT** — chosen because the current Ultralytics stack documents CVAT for YOLO detection workflows (bounding boxes, YOLO import/export, track IDs), and it can run fully offline/self-hosted, which matters for any CCTV-derived imagery with privacy constraints. No other annotation platform is installed for this project (Task 4 §3, §37).

## Class definitions

The authoritative class list lives in `configs/classes.yaml`:

```yaml
classes:
  0: snake
  1: monkey
  2: dog
  3: person
```

Class IDs start at 0, are consecutive, and must never change between dataset versions without a documented migration recorded in `datasets/versions/CHANGELOG.md`. No annotator may introduce a class ID outside this file.

## Bounding-box rules

Draw the **tightest practical box** around the visible object — not a generous box that includes background. A snake's box should hug its visible body, not the whole patch of grass around it.

## Partial / occluded objects

- **Partially visible but identifiable** (e.g. a snake half-hidden in grass, a monkey partly behind a wall): annotate the **visible region** with a bounding box. These examples matter for CCTV robustness — do not discard them.
- **Too occluded to confidently identify**: do not assign a class. Route the sample to `review_required` or `unusable` instead of forcing a guess.

## Very small / distant objects

CCTV footage often contains small, distant animals. Do not remove them automatically. Record `object_scale` (`tiny`/`small`/`medium`/`large`, see `configs/dataset.yaml` → `object_scale_bands`) rather than applying an invented universal pixel threshold. Whether to retain extremely small objects is decided from actual image resolution and annotation quality, case by case.

## Snake annotation — special attention

Prioritize careful review of: coiled snakes, partially hidden snakes, snakes crossing roads, snakes in grass, snakes near walls, snakes under vehicles, distant snakes, low-light snakes, motion-blurred snakes.

**Never annotate a hose, rope, cable, stick, or similar object as `snake`.** These belong in the hard-negative set (`datasets/raw/hard_negatives/`), not as a mislabeled snake.

## Snake sub-category (metadata, not a detection class)

`likely_venomous` / `likely_non_venomous` / `unknown` is recorded as **sample metadata only** when the source reliably supports it — never as an additional YOLO class ID, and never treated as a definitive ground-truth label from uncertain visual identification (Task 4 §13).

## Hard negatives

Images containing no target animal, but objects that could cause false positives — rope, hose, wire, cable, stick, branch, leaf, shadow, plastic pipe, curved object — get **no class label**. Per the project's `empty_label_policy` (`configs/dataset.yaml`), these images simply have no corresponding `.txt` file; this is valid under the Ultralytics YOLO convention, not an error.

## Person annotation

Annotate only the bounding box. **Never** add identity, name, face-identity, or any biometric information to a person annotation — the `person` class exists purely to establish human presence/proximity for future zone-aware risk context, not identification (Task 4 §12, §59).

## Ambiguous objects

If an annotator cannot confidently determine the class or extent of an object, do not force an annotation. Flag it for `review_required` and let a second reviewer decide, rather than guessing.

## Review priority

Manual review time is limited — prioritize: snake examples, small/distant objects, low-light images, occluded objects, blurred/motion-blurred images, and any example an annotator personally found hard to call. These carry the most risk of degrading the model if mislabeled (Task 4 §46).

## Quality control process

```text
Annotation → Automated validation (scripts/dataset/validate_yolo_labels.py etc.) → Human review → Approved
```

For a research-quality subset, independent double-annotation (Annotator A vs. Annotator B) is planned, with IoU used as a bounding-box agreement measure once real annotators and samples exist. No agreement number is claimed until it is actually measured (Task 4 §45).
