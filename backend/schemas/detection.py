"""AI-CCTV Sentinel — Detection & Track data contracts (Layers 4-6).

The detector's class list is intentionally NOT finalized here — see
configs/model.yaml `detector.class_list`. `animal_class` is a free
string on purpose so this contract does not need to change once real
classes are defined.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class Detection(BaseModel):
    """A single per-frame detector output (Layer 4)."""

    camera_id: str
    frame_id: int
    animal_class: str = Field(..., examples=["snake", "monkey", "dog", "person", "other", "unknown"])
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: BoundingBox
    timestamp: datetime


class Track(BaseModel):
    """A tracker's persistent identity for a detected object (Layer 5)."""

    track_id: int
    camera_id: str
    animal_class: str
    first_seen: datetime
    last_seen: datetime
    duration_seconds: float
    detection_count: int = Field(..., ge=0)
    average_confidence: float = Field(..., ge=0.0, le=1.0)


class TemporalVerdict(BaseModel):
    """Output of the temporal-consistency layer for a given track (Layer 6).

    A track only becomes eligible to turn into an Event once
    `confirmed` is True (see configs/risk.yaml `temporal.*`).
    """

    track_id: int
    confirmed: bool
    frames_observed: int
    duration_seconds: float
    minimum_frames_required: int
    minimum_duration_required_seconds: float
