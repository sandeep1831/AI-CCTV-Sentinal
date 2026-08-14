"""AI-CCTV Sentinel — Alert contract (Layer 10)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class AlertChannel(StrEnum):
    LOG = "log"
    DASHBOARD = "dashboard"
    MOBILE_PUSH = "mobile_push"
    IOT_ALARM = "iot_alarm"


class AlertStatus(StrEnum):
    PENDING = "PENDING"
    SENT = "SENT"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    FAILED = "FAILED"


class Alert(BaseModel):
    """A dispatched notification derived from an Event.

    One Event may fan out into multiple Alerts (one per channel), per
    the policy in configs/alerts.yaml.
    """

    alert_id: str = Field(..., examples=["ALT-000042"])
    event_id: str
    channel: AlertChannel
    status: AlertStatus = AlertStatus.PENDING
    created_at: datetime
    acknowledged_at: datetime | None = None
    acknowledged_by: str | None = None
