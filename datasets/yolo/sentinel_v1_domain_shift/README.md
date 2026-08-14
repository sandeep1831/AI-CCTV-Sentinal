# Domain-Shift Evaluation Subset

Status: **insufficient** — no samples currently exist.

Per Task 4 §35/§63, this is an optional evaluation subset intended to
hold conditions that differ from the main `sentinel_v1` training
distribution (e.g. night, rain, a different camera, a different
location/background/resolution). It is kept separate from the
ordinary test set so domain-shift evaluation isn't compromised by
mixing populations.

This subset is not populated as part of dataset v1.0.0 because no
qualifying samples have been collected yet (see
`docs/research/dataset-gap-analysis.md`). It will be filled once
Task 3 collection produces samples that genuinely differ in condition
from the main training set — never fabricated to fill this directory.
