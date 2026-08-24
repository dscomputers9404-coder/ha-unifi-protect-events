from homeassistant.components.event import EventEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DATA_STORE, DOMAIN

EVENT_TYPES = ["person","vehicle","animal","package","face","licensePlate","ring","motion","smartDetectZone"]

async def async_setup_entry(hass, entry, async_add_entities):
    store = hass.data[DOMAIN][entry.entry_id][DATA_STORE]
    async_add_entities([ProtectDetectionEventEntity(entry, store)])

class ProtectDetectionEventEntity(EventEntity):
    _attr_has_entity_name = True
    _attr_name = "Detection"
    _attr_icon = "mdi:cctv"
    _attr_event_types = EVENT_TYPES

    def __init__(self, entry, store):
        self._store = store
        self._attr_unique_id = f"{entry.entry_id}_detection"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="UniFi Protect Events",
            manufacturer="Ubiquiti",
        )

    async def async_added_to_hass(self):
        self.async_on_remove(self._store.subscribe(self._handle_update))

    def _handle_update(self):
        event = self._store.latest
        if event:
            self._trigger_event(event.event_type, event.as_dict())
            self.async_write_ha_state()
