"""AI-CCTV Sentinel — Model registry & lifecycle contract (Layers 26-27).

Defines the states a trained model version can occupy and the
metadata needed to evaluate and roll back safely. No training or
deployment logic is implemented in Task 2 — this is the data contract
those future components will operate on.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ModelState(StrEnum):
    TRAINING = "TRAINING"
    VALIDATING = "VALIDATING"
    CANDIDATE = "CANDIDATE"
    STAGED = "STAGED"
    PRODUCTION = "PRODUCTION"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


class ModelMetrics(BaseModel):
    """Evaluation metrics used to compare a candidate against production.

    See Task 2 §43 (Research Experiment Architecture) for the full
    metric list; not all fields need be populated until real
    evaluation runs exist.
    """

    map50: float | None = Field(default=None, ge=0.0, le=1.0)
    precision: float | None = Field(default=None, ge=0.0, le=1.0)
    recall: float | None = Field(default=None, ge=0.0, le=1.0)
    f1: float | None = Field(default=None, ge=0.0, le=1.0)
    false_positive_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    latency_ms: float | None = Field(default=None, ge=0.0)
    fps: float | None = Field(default=None, ge=0.0)


class ModelVersion(BaseModel):
    """A single registered model version and its lifecycle state."""

    version: str = Field(..., examples=["v1.1.0"])
    state: ModelState
    base_architecture: str = Field(default="yolo26n")
    trained_at: datetime | None = None
    training_run_id: str | None = None
    dataset_version: str | None = None
    metrics: ModelMetrics = Field(default_factory=ModelMetrics)
    promoted_at: datetime | None = None
    rejected_reason: str | None = None
