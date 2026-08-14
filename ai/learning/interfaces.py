"""AI-CCTV Sentinel — Self-learning architecture interfaces (Layer 14).

Task 2 defines ONLY these interfaces and the data flow between them
(Task 2 §23-§27). No algorithm is implemented: not sample selection,
not drift scoring, not training, not deployment decisions. That is
explicitly out of scope until later tasks (Task 2 §47).

Data flow this module's interfaces support:

    Detection -> Human Feedback -> Verified Sample -> Sample Selection
    -> Dataset Version -> Training Run -> Candidate Model -> Evaluation
    -> Deployment Decision
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from backend.schemas.feedback import Feedback
from backend.schemas.model import ModelMetrics, ModelVersion


@dataclass(frozen=True)
class SampleCandidate:
    """A detection/feedback pair flagged as potentially valuable for
    a future training dataset (Task 2 §24)."""

    event_id: str
    reasons: list[str]  # e.g. ["low_confidence", "false_positive", "new_camera"]
    feedback: Feedback | None


class SampleSelectionEngine(ABC):
    """Contract for the (future) active-learning sample selector.

    Candidate criteria per Task 2 §24: low confidence, high
    uncertainty, false positive, new environment, new camera,
    underrepresented class. This interface only defines the shape of
    that selection step — no selection logic is implemented in Task 2.
    """

    @abstractmethod
    def select_candidates(self, since: datetime) -> list[SampleCandidate]:
        """Return samples produced since `since` that are worth routing
        to a human for review/inclusion in the next dataset version."""


@dataclass(frozen=True)
class DriftReport:
    """Output of a drift check (Task 2 §25)."""

    camera_id: str | None  # None = system-wide
    drift_score: float
    threshold: float
    drift_detected: bool
    signals: dict[str, float]  # e.g. {"confidence_distribution": 0.12, ...}
    evaluated_at: datetime


class DriftMonitor(ABC):
    """Contract for the (future) data/model drift monitor.

    Per Task 2 §25, drift detection never triggers retraining
    automatically — a DriftReport only feeds into a human-validated
    retraining decision.
    """

    @abstractmethod
    def check(self, camera_id: str | None = None) -> DriftReport:
        """Compute a current DriftReport, optionally scoped to one camera."""


@dataclass(frozen=True)
class TrainingRun:
    """Metadata for a single (future) training run (Task 2 §23, §26)."""

    training_run_id: str
    dataset_version: str
    base_model_version: str
    started_at: datetime
    completed_at: datetime | None
    resulting_model_version: str | None


class TrainingManager(ABC):
    """Contract for the (future) component that launches and tracks
    training runs. No training logic is implemented in Task 2."""

    @abstractmethod
    def start_training_run(self, dataset_version: str, base_model_version: str) -> TrainingRun:
        """Kick off a training run and return its tracking record."""

    @abstractmethod
    def get_training_run(self, training_run_id: str) -> TrainingRun | None:
        """Retrieve a training run's current status."""


class ModelRegistry(ABC):
    """Contract for the model lifecycle registry (Task 2 §26-§27).

    States: TRAINING -> VALIDATING -> CANDIDATE -> STAGED -> PRODUCTION
    (or REJECTED / ARCHIVED at various points). A new model is NEVER
    automatically promoted to PRODUCTION merely because it finished
    training — promotion requires an explicit, evaluated decision.
    """

    @abstractmethod
    def register(self, model: ModelVersion) -> None:
        """Register a new model version, typically starting in TRAINING."""

    @abstractmethod
    def update_metrics(self, version: str, metrics: ModelMetrics) -> None:
        """Attach evaluation metrics to a model version."""

    @abstractmethod
    def promote(self, version: str) -> None:
        """Advance a model version to PRODUCTION. Must only be called
        after an explicit, evaluated deployment decision (Task 2 §27)."""

    @abstractmethod
    def reject(self, version: str, reason: str) -> None:
        """Mark a candidate model version as REJECTED, leaving the
        current PRODUCTION model untouched."""

    @abstractmethod
    def rollback(self, to_version: str) -> None:
        """Revert PRODUCTION to a previously validated model version."""

    @abstractmethod
    def get_production_version(self) -> ModelVersion | None:
        """Return whichever model version currently serves PRODUCTION
        traffic, if any."""
