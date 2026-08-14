"""AI-CCTV Sentinel — Camera & Zone data contracts (Layer 1).

These schemas define the SHAPE of camera/zone data used across the
architecture. No real camera credentials are modeled here — a camera's
stream URL is always resolved from an environment variable at runtime,
never stored as a literal secret in these objects.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class CameraStatus(StrEnum):
    """Runtime health of a camera stream (Layer: Camera Failure Handling)."""

    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    RECONNECTING = "RECONNECTING"


class Zone(BaseModel):
    """A logical area within a camera's field of view."""

    id: str = Field(..., examples=["CORRIDOR-A1"])
    kind: str = Field(..., examples=["corridor", "classroom", "playground", "restricted"])
    student_access: bool = True
    restricted: bool = False


class Camera(BaseModel):
    """Metadata for a single existing CCTV camera reused by the system."""

    camera_id: str = Field(..., examples=["CAM-001"])
    name: str = Field(..., examples=["Block-A-Corridor"])
    location: str = Field(..., examples=["Academic Block A"])
    zone_ids: list[str] = Field(default_factory=list)
    stream_type: str = Field(default="rtsp")
    resolution: str | None = Field(default=None, examples=["1920x1080"])
    fps: int | None = Field(default=None, ge=1, le=60)
    enabled: bool = False
    status: CameraStatus = CameraStatus.OFFLINE
