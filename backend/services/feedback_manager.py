"""AI-CCTV Sentinel — FeedbackManager interface (Layer 13: Human-in-the-Loop).

Captures CONFIRM / DISMISS / UNCERTAIN judgments from an authorized
human reviewer for a given Event. This feedback is the raw input to
the (future, not implemented in Task 2) active-learning sample
selection engine — see ai/learning/interfaces.py.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.schemas.feedback import Feedback, FeedbackOutcome


class FeedbackManager(ABC):
    """Contract for recording and retrieving human feedback on events."""

    @abstractmethod
    def submit_feedback(
        self,
        event_id: str,
        outcome: FeedbackOutcome,
        reviewed_by: str,
        reason: str | None = None,
    ) -> Feedback:
        """Record a human's judgment on an event."""

    @abstractmethod
    def get_feedback_for_event(self, event_id: str) -> Feedback | None:
        """Retrieve the feedback recorded for a given event, if any."""
