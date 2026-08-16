"""AI-CCTV Sentinel — Specialist result contract (Task 6 §42).

Python/Pydantic counterpart to schemas/specialist_result.schema.json.
Common output contract for the snake classification and dog
visible-health screening branches. This is a SCREENING result, never
a diagnosis: `diagnosis` is always False, and confidence is model
confidence in the visual class only — never a medical/venom
probability (Task 6 §19, §34, §59).

Task 7 (dog behavior + audio) and later risk-engine consumption are
anticipated by the `MultimodalDogResult` wrapper at the bottom of this
file, with `behavior`/`audio` explicitly `NOT_AVAILABLE` in Task 6
(Task 6 §41) — never fabricated.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class SpecialistType(StrEnum):
    SNAKE_CLASSIFICATION = "snake_classification"
    VISIBLE_HEALTH_SCREENING = "visible_health_screening"


class SnakeCategory(StrEnum):
    LIKELY_VENOMOUS = "likely_venomous"
    LIKELY_NON_VENOMOUS = "likely_non_venomous"
    UNKNOWN = "unknown"


class DogHealthCategory(StrEnum):
    NORMAL_VISIBLE_APPEARANCE = "normal_visible_appearance"
    POSSIBLE_WOUND = "possible_wound"
    POSSIBLE_SKIN_ABNORMALITY = "possible_skin_abnormality"
    POSSIBLE_INJURY = "possible_injury"
    UNABLE_TO_ASSESS = "unable_to_assess"


class Visibility(StrEnum):
    SUFFICIENT = "sufficient"
    FULL_BODY_VISIBLE = "full_body_visible"
    PARTIAL_BODY_VISIBLE = "partial_body_visible"
    INSUFFICIENT_VISIBILITY = "insufficient_visibility"


class Recommendation(StrEnum):
    VETERINARY_REVIEW = "veterinary_review"
    HUMAN_REVIEW = "human_review"


class SpecialistStatus(StrEnum):
    VALID = "valid"
    INVALID = "invalid"


# Safety-sensitive predictions that must default review_required=True
# (Task 6 §43-44, §58).
_REVIEW_REQUIRED_PREDICTIONS = {
    SnakeCategory.LIKELY_VENOMOUS.value,
    DogHealthCategory.POSSIBLE_WOUND.value,
    DogHealthCategory.POSSIBLE_SKIN_ABNORMALITY.value,
    DogHealthCategory.POSSIBLE_INJURY.value,
}


class Region(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class SpecialistResult(BaseModel):
    """Common output contract for every specialist branch."""

    animal: str = Field(..., examples=["snake", "dog"])
    specialist_type: SpecialistType
    prediction: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    visibility: Visibility
    source_detection_id: str = Field(..., examples=["DET-00123"])
    model_version: str = Field(..., examples=["snake-cls-v1.0.0", "dog-health-v1.0.0"])
    timestamp: datetime

    secondary_prediction: str | None = None
    region: Region | None = None
    review_required: bool = False
    diagnosis: bool = Field(default=False, frozen=True)
    recommendation: Recommendation | None = None
    specialist_status: SpecialistStatus = SpecialistStatus.VALID

    @field_validator("diagnosis")
    @classmethod
    def _diagnosis_must_be_false(cls, value: bool) -> bool:
        if value is not False:
            raise ValueError(
                "diagnosis must always be False — a specialist result is a "
                "screening output, never a veterinary/medical diagnosis "
                "(Task 6 §2, §33)."
            )
        return value

    @classmethod
    def build(
        cls,
        *,
        animal: str,
        specialist_type: SpecialistType,
        prediction: str,
        confidence: float,
        visibility: Visibility,
        source_detection_id: str,
        model_version: str,
        timestamp: datetime,
        secondary_prediction: str | None = None,
        region: Region | None = None,
    ) -> "SpecialistResult":
        """Convenience constructor that applies the review_required default
        policy automatically instead of leaving callers to remember it."""

        return cls(
            animal=animal,
            specialist_type=specialist_type,
            prediction=prediction,
            confidence=confidence,
            visibility=visibility,
            source_detection_id=source_detection_id,
            model_version=model_version,
            timestamp=timestamp,
            secondary_prediction=secondary_prediction,
            region=region,
            review_required=prediction in _REVIEW_REQUIRED_PREDICTIONS,
            recommendation=(
                Recommendation.VETERINARY_REVIEW
                if prediction in _REVIEW_REQUIRED_PREDICTIONS
                else None
            ),
        )


class NotAvailable(BaseModel):
    """Explicit placeholder for a Task-7+ modality that is intentionally
    not implemented yet. Distinguishes "we checked and there's nothing
    to report" from "this feature doesn't exist yet" — never silently
    omitted or fabricated (Task 6 §41)."""

    status: str = "NOT_AVAILABLE"
    reason: str = "Not implemented until a later task."


class MultimodalDogResult(BaseModel):
    """Forward-looking wrapper anticipating Task 7's behavior/audio
    fields. In Task 6, `behavior` and `audio` are always NotAvailable —
    this class exists so the eventual Task 7 integration doesn't require
    reshaping the Task 6 contract, per Task 6 §41."""

    animal: str = "dog"
    detection: dict = Field(default_factory=dict)
    health: SpecialistResult | None = None
    behavior: NotAvailable = Field(default_factory=NotAvailable)
    audio: NotAvailable = Field(default_factory=NotAvailable)
    risk: NotAvailable = Field(
        default_factory=lambda: NotAvailable(reason="Risk scoring belongs to Task 10, not Task 6.")
    )
