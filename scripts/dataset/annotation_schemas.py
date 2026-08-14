"""AI-CCTV Sentinel — annotation, quality, grouping & split schemas (Task 4).

Companion to scripts/dataset/schemas.py (Task 3's source/sample
provenance schemas). This module covers the Task 4 concerns: YOLO
label records, image quality metrics, leakage-prevention grouping,
and split assignment.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# YOLO label validation (Task 4 §16, §19-23)
# ---------------------------------------------------------------------------


class LabelIssue(StrEnum):
    WRONG_FIELD_COUNT = "wrong_field_count"
    NON_NUMERIC_VALUE = "non_numeric_value"
    INVALID_CLASS_ID = "invalid_class_id"
    X_CENTER_OUT_OF_RANGE = "x_center_out_of_range"
    Y_CENTER_OUT_OF_RANGE = "y_center_out_of_range"
    WIDTH_OUT_OF_RANGE = "width_out_of_range"
    HEIGHT_OUT_OF_RANGE = "height_out_of_range"
    NON_POSITIVE_WIDTH = "non_positive_width"
    NON_POSITIVE_HEIGHT = "non_positive_height"
    BOX_EXCEEDS_IMAGE_BOUNDS = "box_exceeds_image_bounds"


class YoloBoxLabel(BaseModel):
    """A single parsed YOLO-format label line."""

    class_id: int
    x_center: float
    y_center: float
    width: float
    height: float

    def to_corners(self) -> tuple[float, float, float, float]:
        """Return (x_min, y_min, x_max, y_max) in normalized 0-1 coords."""

        x_min = self.x_center - self.width / 2
        y_min = self.y_center - self.height / 2
        x_max = self.x_center + self.width / 2
        y_max = self.y_center + self.height / 2
        return x_min, y_min, x_max, y_max


class LabelFileValidationResult(BaseModel):
    label_path: str
    image_path: str | None = None
    boxes: list[YoloBoxLabel] = Field(default_factory=list)
    issues: list[LabelIssue] = Field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.issues


# ---------------------------------------------------------------------------
# Image/label pairing (Task 4 §22)
# ---------------------------------------------------------------------------


class PairingIssue(StrEnum):
    MISSING_IMAGE = "missing_image"
    MISSING_LABEL = "missing_label"
    ORPHAN_LABEL = "orphan_label"
    DUPLICATE_LABEL = "duplicate_label"


class ImageLabelPair(BaseModel):
    image_path: str | None
    label_path: str | None
    split: str  # train | val | test
    issues: list[PairingIssue] = Field(default_factory=list)
    # A negative/hard-negative image with no label file is VALID per
    # the documented empty_label_policy (configs/dataset.yaml), not an
    # issue, as long as that omission is intentional (image exists,
    # label legitimately doesn't).


# ---------------------------------------------------------------------------
# Image quality (Task 4 §26-29)
# ---------------------------------------------------------------------------


class QualityFlag(StrEnum):
    GOOD = "good"
    REVIEW = "review"
    REJECT = "reject"


class ObjectScale(StrEnum):
    TINY = "tiny"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class ImageQualityMetrics(BaseModel):
    image_path: str
    width: int | None = None
    height: int | None = None
    aspect_ratio: float | None = None
    blur_score: float | None = None  # variance of Laplacian
    brightness_score: float | None = None  # mean pixel intensity, 0-255
    contrast_score: float | None = None  # std of pixel intensity
    quality_flag: QualityFlag = QualityFlag.GOOD
    notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Leakage-prevention grouping (Task 4 §31-32)
# ---------------------------------------------------------------------------


class GroupAssignment(BaseModel):
    """Maps a file to the group it must stay bundled with across splits."""

    path: str
    group_id: str = Field(..., examples=["source_video_id:CAM-001_20260811_1", "source_dataset:DS-PUBLIC-001"])
    group_kind: str = Field(..., examples=["sequence", "source_dataset", "singleton"])


class SplitName(StrEnum):
    TRAIN = "train"
    VAL = "val"
    TEST = "test"


class SplitAssignment(BaseModel):
    group_id: str
    split: SplitName
    file_count: int = Field(default=0, ge=0)


# ---------------------------------------------------------------------------
# Quarantine (Task 4 §56-57)
# ---------------------------------------------------------------------------


class QuarantineReason(StrEnum):
    CORRUPT = "corrupt"
    DUPLICATE = "duplicate"
    INVALID_ANNOTATION = "invalid_annotation"
    LICENSE_ISSUE = "license_review"
    POOR_QUALITY = "quality_review"


class QuarantineRecord(BaseModel):
    original_path: str
    quarantined_path: str
    reason: QuarantineReason
    detail: str | None = None
    quarantined_at: datetime
