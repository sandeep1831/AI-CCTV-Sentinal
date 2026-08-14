"""AI-CCTV Sentinel — Classifier interface (Layer 7: Classification).

Supports the three ablation modes defined in Task 2 §12 (configs/model.yaml
`classification.mode`):
    Mode A — detector only (Classifier is not invoked)
    Mode B — detector + general classifier
    Mode C — detector + classifier + specialist snake classifier

A classifier refines a detector's crop into a more specific category;
it never claims species-level medical certainty (Task 2 §11 / §46).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ClassificationResult:
    category: str  # e.g. "snake", "monkey", "likely_venomous", "unknown"
    confidence: float


class Classifier(ABC):
    """Contract for any second-stage (or specialist) classifier."""

    @abstractmethod
    def load(self) -> None:
        """Load classifier weights, if any (see configs/model.yaml)."""

    @abstractmethod
    def classify(self, crop: np.ndarray) -> ClassificationResult:
        """Classify a bounding-box crop into a refined category."""
