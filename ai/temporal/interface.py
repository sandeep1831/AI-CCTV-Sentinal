"""AI-CCTV Sentinel — TemporalValidator interface (Layer 6: Temporal Consistency).

Reduces false alarms by requiring a track to persist for a minimum
number of frames and a minimum duration (configs/risk.yaml
`temporal.*`) before it is eligible to become an Event. This is the
consecutive-frame confirmation mechanism referenced by the uploaded
reference paper.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.schemas.detection import TemporalVerdict, Track


class TemporalValidator(ABC):
    """Contract for the component that decides whether a track is
    persistent enough to be treated as a real, confirmed event."""

    @abstractmethod
    def evaluate(self, track: Track) -> TemporalVerdict:
        """Return whether `track` currently satisfies the configured
        minimum-frames and minimum-duration thresholds."""
