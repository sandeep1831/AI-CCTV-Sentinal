"""AI-CCTV Sentinel — AlertManager interface (Layer 10: Alert Manager).

Fans an Event out into zero or more channel-specific Alerts according
to the configurable policy in configs/alerts.yaml (risk level ->
channels). Channel implementations (dashboard push, mobile push, IoT
alarm) are NOT implemented in Task 2 — only this dispatch contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.schemas.alert import Alert, AlertChannel
from backend.schemas.event import Event


class AlertChannelSender(ABC):
    """Contract for a single alert channel's delivery mechanism."""

    channel: AlertChannel

    @abstractmethod
    def send(self, event: Event, alert: Alert) -> None:
        """Deliver `alert` for `event` over this channel."""


class AlertManager(ABC):
    """Contract for the component that decides and dispatches alerts
    for a given Event, based on its risk level."""

    @abstractmethod
    def dispatch(self, event: Event) -> list[Alert]:
        """Determine which channels apply to `event.risk.risk_level`
        (configs/alerts.yaml `policy`) and dispatch to each, returning
        the resulting Alert records."""

    @abstractmethod
    def acknowledge(self, event_id: str, acknowledged_by: str) -> None:
        """Record human acknowledgement of the alert(s) for an event."""
