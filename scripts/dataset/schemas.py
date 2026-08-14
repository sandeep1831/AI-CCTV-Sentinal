"""AI-CCTV Sentinel — dataset metadata schemas (Task 3).

Shared, typed records used by every script under scripts/dataset/.
These mirror the field lists specified in Task 3 (§7 license tracking,
§14 sample metadata, §36 active-learning metadata) so that every tool
writes and reads the same shape.

This module defines schema only. It does not fetch, download, or
fabricate any data.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerated vocabularies (Task 3 §9, §10, §11, §16, §21)
# ---------------------------------------------------------------------------


class Region(StrEnum):
    TELANGANA = "Telangana"
    ANDHRA_PRADESH = "Andhra Pradesh"
    INDIA = "India"
    OTHER_INDIA = "Other India"
    INTERNATIONAL = "International"
    UNKNOWN = "Unknown"


class Lighting(StrEnum):
    DAYLIGHT = "daylight"
    OVERCAST = "overcast"
    LOW_LIGHT = "low_light"
    NIGHT = "night"
    ARTIFICIAL_LIGHT = "artificial_light"
    UNKNOWN = "unknown"


class Weather(StrEnum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    WET = "wet"
    DRY = "dry"
    UNKNOWN = "unknown"


class TimeOfDay(StrEnum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"
    UNKNOWN = "unknown"


class OcclusionLevel(StrEnum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MediaType(StrEnum):
    IMAGE = "image"
    VIDEO = "video"
    FRAME = "frame"


class Quality(StrEnum):
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    UNUSABLE = "unusable"


class HumanReviewStatus(StrEnum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    NOT_APPLICABLE = "not_applicable"


class SourceCategory(StrEnum):
    """Which of datasets/raw/<category>/ this source's samples live under."""

    PUBLIC = "public"
    REGIONAL = "regional"
    CCTV_LIKE = "cctv_like"
    STAGED = "staged"
    FEEDBACK = "feedback"
    HARD_NEGATIVE = "hard_negatives"


# ---------------------------------------------------------------------------
# Dataset source record (Task 3 §6, §7, §13)
# ---------------------------------------------------------------------------


class DatasetSource(BaseModel):
    """One external or internally-collected dataset source.

    One record per distinct source (e.g. one public dataset, one
    campus pilot collection run, one hard-negative collection batch)
    — not per individual file.
    """

    dataset_id: str = Field(..., examples=["DS-PUBLIC-001"])
    name: str
    source_url: str | None = None
    publisher: str | None = None
    license: str = Field(..., examples=["CC-BY-4.0", "Unknown — pending review"])
    commercial_use: bool | None = None
    redistribution_allowed: bool | None = None
    research_use: bool | None = None
    attribution_required: bool | None = None
    category: SourceCategory
    task: str = Field(..., examples=["detection", "classification"])
    classes: list[str] = Field(default_factory=list)
    image_count: int = Field(default=0, ge=0)
    video_count: int = Field(default=0, ge=0)
    resolution: str | None = None
    region: Region = Region.UNKNOWN
    collection_conditions: str | None = None
    collection_method: str | None = None
    download_date: date | None = None
    usage_restrictions: str | None = None


# ---------------------------------------------------------------------------
# Sample-level metadata (Task 3 §14, §21, §36)
# ---------------------------------------------------------------------------


class SampleMetadata(BaseModel):
    """Per-file metadata. One record per collected image/video/frame."""

    sample_id: str = Field(..., examples=["SNAKE-000001"])
    dataset_id: str
    source_id: str | None = None
    original_filename: str
    media_type: MediaType
    animal_class: str = Field(..., examples=["snake", "monkey", "dog", "person", "hard_negative", "background"])
    snake_category: str | None = Field(
        default=None, examples=["likely_venomous", "likely_non_venomous", "unknown"]
    )
    region: Region = Region.UNKNOWN
    camera_type: str | None = None
    resolution: str | None = None
    lighting: Lighting = Lighting.UNKNOWN
    weather: Weather = Weather.UNKNOWN
    time_of_day: TimeOfDay = TimeOfDay.UNKNOWN
    viewpoint: str | None = Field(default=None, examples=["top_down", "elevated", "eye_level", "ground_level"])
    occlusion_level: OcclusionLevel = OcclusionLevel.NONE
    quality: Quality = Quality.ACCEPTABLE
    license: str | None = None
    sha256: str | None = None
    phash: str | None = None
    collected_at: datetime | None = None

    # Future active-learning metadata (Task 3 §36) — populated later,
    # not during Task 3 collection.
    uncertainty_score: float | None = Field(default=None, ge=0.0, le=1.0)
    selection_reason: str | None = None
    human_review_status: HumanReviewStatus = HumanReviewStatus.NOT_APPLICABLE
    feedback_label: str | None = None
    model_version: str | None = None


# ---------------------------------------------------------------------------
# Validation / quality-gate results (Task 3 §16, §39, §47)
# ---------------------------------------------------------------------------


class ValidationIssue(StrEnum):
    CORRUPT_IMAGE = "corrupt_image"
    UNSUPPORTED_EXTENSION = "unsupported_extension"
    ZERO_BYTE_FILE = "zero_byte_file"
    MISSING_METADATA = "missing_metadata"
    DUPLICATE_FILENAME = "duplicate_filename"
    INVALID_DIMENSIONS = "invalid_dimensions"
    DUPLICATE_HASH = "duplicate_hash"


class FileValidationResult(BaseModel):
    path: str
    readable: bool
    issues: list[ValidationIssue] = Field(default_factory=list)
    quality: Quality = Quality.UNUSABLE

    @property
    def passed(self) -> bool:
        return self.readable and not self.issues and self.quality != Quality.UNUSABLE
