"""AI-CCTV Sentinel — data contracts (schemas).

These Pydantic models are the typed contracts shared across AI,
backend, alerting, storage, and (future) learning components. They
define SHAPE only — Task 2 does not implement persistence or business
logic against them.
"""

from backend.schemas.alert import Alert, AlertChannel, AlertStatus
from backend.schemas.camera import Camera, CameraStatus, Zone
from backend.schemas.detection import BoundingBox, Detection, TemporalVerdict, Track
from backend.schemas.event import Event, RiskAssessment, RiskLevel
from backend.schemas.feedback import Feedback, FeedbackOutcome
from backend.schemas.model import ModelMetrics, ModelState, ModelVersion

__all__ = [
    "Alert",
    "AlertChannel",
    "AlertStatus",
    "Camera",
    "CameraStatus",
    "Zone",
    "BoundingBox",
    "Detection",
    "TemporalVerdict",
    "Track",
    "Event",
    "RiskAssessment",
    "RiskLevel",
    "Feedback",
    "FeedbackOutcome",
    "ModelMetrics",
    "ModelState",
    "ModelVersion",
]
