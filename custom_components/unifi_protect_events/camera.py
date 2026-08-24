from homeassistant.components.camera import Camera
from homeassistant.helpers.entity import DeviceInfo
from .const import DATA_STORE, DOMAIN, RECENT_CAMERA_SLOTS

async def async_setup_entry(hass, entry, async_add_entities):
    store = hass.data[DOMAIN][entry.entry_id][DATA_STORE]
    async_add_entities([
        ProtectRecentDetectionCamera(entry, store, i)
        for i in range(RECENT_CAMERA_SLOTS)
    ])

class ProtectRecentDetectionCamera(Camera):
    _attr_has_entity_name = True
    _attr_icon = "mdi:cctv"
    _attr_content_type = "image/jpeg"

    def __init__(self, entry, store, index):
        super().__init__()
        self._store = store
        self._index = index
        self._attr_name = f"Detection {index + 1}"
        self._attr_unique_id = f"{entry.entry_id}_detection_{index + 1}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="UniFi Protect Events",
            manufacturer="Ubiquiti",
        )

    async def async_added_to_hass(self):
        self.async_on_remove(self._store.subscribe(self.async_write_ha_state))

    @property
    def available(self):
        event = self._store.event_at(self._index)
        return event is not None and event.snapshot is not None

    async def async_camera_image(self, width=None, height=None):
        event = self._store.event_at(self._index)
        return event.snapshot if event else None

    @property
    def extra_state_attributes(self):
        event = self._store.event_at(self._index)
        return event.as_dict() if event else {
            "event_type": None,
            "camera_name": None,
            "timestamp": None,
        }
