# Model Selection

**Status: PENDING.** No trained candidates exist to compare. This document will explain the selected model using accuracy (mAP50-95), snake recall (safety priority — Task 5 §62), false-positive behavior, latency, and resource usage, once EXP-001 (and any follow-on experiments) actually complete.

Selection rule (policy, defined now, applied later): a candidate is chosen using mAP50-95 as the primary metric, snake recall as a safety-weighted factor, false-positive behavior as a practical factor, and inference latency as a deployment factor — never from a single metric alone (Task 5 §61-62). A model with marginally higher overall mAP but substantially worse snake recall does not automatically win.
