"""AI-CCTV Sentinel — Tracker interface (Layer 5: Object Tracking).

Both BoT-SORT and ByteTrack (as documented by the current Ultralytics
stack) must be able to satisfy this same interface so they can be
swapped and compared experimentally (Task 2 §9) without changing the
detector or anything downstream.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.schemas.detection import Detection, Track


class Tracker(ABC):
    """Contract for any multi-object tracker used in the pipeline."""

    @abstractmethod
    def update(self, camera_id: str, detections: list[Detection]) -> list[Track]:
        """Associate a new frame's detections with existing/new tracks.

        Must be called once per processed frame, in order, for a given
        camera_id. Returns the current state of all active tracks for
        that camera after incorporating the new detections.
        """

    @abstractmethod
    def reset(self, camera_id: str) -> None:
        """Clear all track state for a camera (e.g. after a reconnect)."""
