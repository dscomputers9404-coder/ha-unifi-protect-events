from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DATA_STORE, DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    store = hass.data[DOMAIN][entry.entry_id][DATA_STORE]
    async_add_entities([ProtectRecentEventsSensor(entry, store)])

class ProtectRecentEventsSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Recent detections"
    _attr_icon = "mdi:cctv"

    def __init__(self, entry, store):
        self._store = store
        self._attr_unique_id = f"{entry.entry_id}_recent_events"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="UniFi Protect Events",
            manufacturer="Ubiquiti",
        )

    async def async_added_to_hass(self):
        self.async_on_remove(self._store.subscribe(self.async_write_ha_state))

    @property
    def native_value(self):
        return len(self._store.events)

    @property
    def extra_state_attributes(self):
        return {
            "latest": self._store.latest.as_dict() if self._store.latest else None,
            "events": [e.as_dict() for e in self._store.events[:20]],
        }
