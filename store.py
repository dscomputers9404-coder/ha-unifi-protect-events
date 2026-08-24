from collections import deque
import logging

from homeassistant.helpers.storage import Store

from .const import (
    EVENT_MERGE_WINDOW_SECONDS,
    MAX_EVENTS,
    RECENT_CAMERA_SLOTS,
    SMART_DETECTION_TYPES,
)
from .models import ProtectDetection

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_SAVE_DELAY_SECONDS = 2


class ProtectEventStore:
    def __init__(self, hass, entry_id):
        self._events = deque(maxlen=MAX_EVENTS)
        self._listeners = set()
        self._storage = Store(
            hass,
            STORAGE_VERSION,
            f"unifi_protect_events.{entry_id}.recent_detections",
        )

    @property
    def events(self):
        return list(self._events)

    @property
    def latest(self):
        return self._events[0] if self._events else None

    def event_at(self, index):
        events = self.events
        return events[index] if 0 <= index < len(events) else None

    async def async_load(self):
        """Restore recent detections and snapshots after a HA restart."""
        data = await self._storage.async_load()
        if not isinstance(data, dict):
            return

        saved_events = data.get("events")
        if not isinstance(saved_events, list):
            return

        restored = []
        for item in saved_events[:RECENT_CAMERA_SLOTS]:
            event = ProtectDetection.from_storage_dict(item)
            if event is not None:
                restored.append(event)

        self._events = deque(restored, maxlen=MAX_EVENTS)
        if restored:
            _LOGGER.info("Restored %s recent UniFi Protect detections", len(restored))

    def _data_to_save(self):
        # Persist only what is used by the recent-detection camera slots.
        # This keeps Home Assistant storage small, even on busy cameras.
        return {
            "events": [
                event.as_storage_dict()
                for event in list(self._events)[:RECENT_CAMERA_SLOTS]
            ]
        }

    def _schedule_save(self):
        self._storage.async_delay_save(
            self._data_to_save,
            STORAGE_SAVE_DELAY_SECONDS,
        )

    @staticmethod
    def _same_camera_close_in_time(first, second):
        if not first.camera_id or first.camera_id != second.camera_id:
            return False

        try:
            delta = abs((first.timestamp - second.timestamp).total_seconds())
        except (AttributeError, TypeError):
            return False

        return delta <= EVENT_MERGE_WINDOW_SECONDS

    def _notify(self):
        for listener in list(self._listeners):
            listener()

    def _changed(self):
        self._schedule_save()
        self._notify()

    def add(self, event):
        # Never store the exact same Protect event twice.
        if any(existing.event_id == event.event_id for existing in self._events):
            return

        is_smart = event.event_type in SMART_DETECTION_TYPES

        if is_smart:
            # Protect often sends `motion` first and the classified event
            # (person/vehicle/animal/...) shortly afterwards. Replace the
            # generic motion thumbnail with the smart detection.
            motion_match = next(
                (
                    existing
                    for existing in self._events
                    if existing.event_type == "motion"
                    and self._same_camera_close_in_time(existing, event)
                ),
                None,
            )
            if motion_match is not None:
                self._events.remove(motion_match)
                self._events.appendleft(event)
                self._changed()
                return

        elif event.event_type == "motion":
            # If generic motion arrives after a nearby smart detection, ignore it
            # so the classified thumbnail is not followed by a MOTION duplicate.
            if any(
                existing.event_type in SMART_DETECTION_TYPES
                and self._same_camera_close_in_time(existing, event)
                for existing in self._events
            ):
                return

        self._events.appendleft(event)
        self._changed()

    def subscribe(self, listener):
        self._listeners.add(listener)

        def unsubscribe():
            self._listeners.discard(listener)

        return unsubscribe
