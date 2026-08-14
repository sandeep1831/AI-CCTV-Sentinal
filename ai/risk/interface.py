"""AI-CCTV Sentinel — RiskEngine interface (Layer 8: Risk Assessment).

Turns a confirmed, classified detection into a risk_score / risk_level
/ reason triple (backend.schemas.event.RiskAssessment). The scoring
formula and thresholds are configuration-driven
(configs/risk.yaml) — this interface must not hard-code them.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.schemas.camera import Zone
from backend.schemas.detection import Track
from backend.schemas.event import RiskAssessment


class RiskEngine(ABC):
    """Contract for the component that scores a confirmed track."""

    @abstractmethod
    def assess(self, track: Track, zone: Zone | None) -> RiskAssessment:
        """Compute a RiskAssessment for a temporally-confirmed track,
        optionally taking the zone it was detected in into account."""
