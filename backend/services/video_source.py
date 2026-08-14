"""AI-CCTV Sentinel — VideoSource interface (Layer 2: Video Ingestion).

Architecture-only for Task 2: this defines the CONTRACT a video
source must satisfy (RTSP camera, local file, or recorded clip for
development) so that every downstream component (frame processing,
detection, tracking, ...) can depend on this interface instead of a
concrete OpenCV/FFmpeg implementation.

No real RTSP connection logic is implemented here yet — see
configs/video.yaml for the reconnect/heartbeat parameters this
interface is expected to honor once implemented.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

import numpy as np


class StreamHealth(StrEnum):
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    RECONNECTING = "RECONNECTING"


@dataclass(frozen=True)
class Frame:
    """A single timestamped frame read from a video source."""

    camera_id: str
    frame_id: int
    image: np.ndarray
    captured_at: datetime


class VideoSource(ABC):
    """Contract for anything that can produce a stream of frames.

    Concrete implementations (RTSP camera, local video file, recorded
    test clip) all satisfy this same interface, so the rest of the
    pipeline never depends on OpenCV/FFmpeg directly.
    """

    @abstractmethod
    def open(self) -> None:
        """Establish the underlying connection/handle."""

    @abstractmethod
    def read(self) -> Frame | None:
        """Return the next available frame, or None if none is ready."""

    @abstractmethod
    def health(self) -> StreamHealth:
        """Return the current connection health (drives reconnect logic)."""

    @abstractmethod
    def close(self) -> None:
        """Release the underlying connection/handle."""
