"""AI-CCTV Sentinel — Event contract (Layer 9).

Event is the central abstraction of the whole system: every
temporally-confirmed, risk-scored detection becomes one Event, and
every downstream component (alerts, storage, dashboard, feedback,
learning) consumes this same shape. This is the object referenced by
Task 2 §16 and §50 ("clean interfaces" / "common contract").
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskAssessment(BaseModel):
    """Output of the Risk Assessment Engine (Layer 8)."""

    risk_score: int = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    reason: list[str] = Field(default_factory=list)


class Event(BaseModel):
    """A confirmed, risk-scored detection event.

    This is the object handed from AI -> Event Manager -> Alert
    Manager -> Backend API -> Storage -> Dashboard/Mobile ->
    Feedback -> (future) Active Learning.
    """

    event_id: str = Field(..., examples=["EVT-000102"])
    camera_id: str
    zone_id: str | None = None
    track_id: int
    animal_class: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    risk: RiskAssessment
    timestamp: datetime
    model_version: str

    # Populated once a snapshot/clip is captured for this event.
    # Raw continuous video is never stored — see
    # docs/architecture/security-architecture.md (Privacy Architecture).
    snapshot_uri: str | None = None
