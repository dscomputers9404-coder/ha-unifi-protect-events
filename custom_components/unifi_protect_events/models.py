import base64
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class ProtectDetection:
    event_id: str
    event_type: str
    camera_id: str | None
    camera_name: str | None
    timestamp: datetime
    confidence: int | float | None = None
    zones: list[Any] = field(default_factory=list)
    snapshot: bytes | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def as_dict(self):
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "camera_id": self.camera_id,
            "camera_name": self.camera_name,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
            "zones": self.zones,
            "has_snapshot": self.snapshot is not None,
        }

    def as_storage_dict(self):
        """Return a JSON-serialisable representation, including the snapshot."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "camera_id": self.camera_id,
            "camera_name": self.camera_name,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
            "zones": self.zones,
            "snapshot": (
                base64.b64encode(self.snapshot).decode("ascii")
                if self.snapshot is not None
                else None
            ),
        }

    @classmethod
    def from_storage_dict(cls, data):
        """Restore an event that was stored by as_storage_dict()."""
        if not isinstance(data, dict):
            return None

        try:
            timestamp = datetime.fromisoformat(str(data["timestamp"]).replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError):
            return None

        snapshot = None
        encoded_snapshot = data.get("snapshot")
        if isinstance(encoded_snapshot, str) and encoded_snapshot:
            try:
                snapshot = base64.b64decode(encoded_snapshot)
            except (ValueError, TypeError):
                snapshot = None

        event_id = data.get("event_id")
        event_type = data.get("event_type")
        if not event_id or not event_type:
            return None

        return cls(
            event_id=str(event_id),
            event_type=str(event_type),
            camera_id=(str(data["camera_id"]) if data.get("camera_id") else None),
            camera_name=(str(data["camera_name"]) if data.get("camera_name") else None),
            timestamp=timestamp,
            confidence=data.get("confidence"),
            zones=data.get("zones") if isinstance(data.get("zones"), list) else [],
            snapshot=snapshot,
            raw={},
        )
