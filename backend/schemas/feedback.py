"""AI-CCTV Sentinel — Human feedback contract (Layer 13).

This is only the interface/data shape. The learning pipeline that
consumes this feedback (active learning, drift monitoring,
retraining) is architecturally defined but NOT implemented in Task 2
— see docs/architecture/self-learning-architecture.md.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class FeedbackOutcome(StrEnum):
    CONFIRM = "CONFIRM"
    DISMISS = "DISMISS"
    UNCERTAIN = "UNCERTAIN"


class Feedback(BaseModel):
    """A human's judgment on a specific Event.

    Confirmed/dismissed feedback is the raw material for the future
    active-learning sample-selection engine (Task 2 §24) — dismissed
    events in particular become candidate hard-negative examples.
    """

    feedback_id: str = Field(..., examples=["FBK-000031"])
    event_id: str
    outcome: FeedbackOutcome
    reason: str | None = Field(default=None, examples=["Garden hose, not a snake"])
    reviewed_by: str
    reviewed_at: datetime

    # Set by the (future) active-learning sample selection engine once
    # this feedback is chosen for inclusion in a training dataset.
    used_in_training_run_id: str | None = None
