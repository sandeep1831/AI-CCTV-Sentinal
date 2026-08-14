"""AI-CCTV Sentinel — EventManager interface (Layer 9: Event Manager).

Turns a temporally-confirmed, risk-scored track into the canonical
`Event` object (backend.schemas.event.Event) — the common contract
consumed by alerting, storage, dashboard/mobile, and (future)
feedback/learning components.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.schemas.detection import Track
from backend.schemas.event import Event, RiskAssessment


class EventManager(ABC):
    """Contract for the component that creates and retrieves Events."""

    @abstractmethod
    def create_event(
        self,
        track: Track,
        risk: RiskAssessment,
        zone_id: str | None,
        model_version: str,
    ) -> Event:
        """Create and persist (in later tasks) a new Event from a
        confirmed track and its risk assessment."""

    @abstractmethod
    def get_event(self, event_id: str) -> Event | None:
        """Retrieve a previously created Event by id."""
