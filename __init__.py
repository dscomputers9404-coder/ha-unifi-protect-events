import asyncio
from homeassistant.const import CONF_API_KEY, CONF_HOST
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ProtectApiClient
from .const import (
    CONF_VERIFY_SSL, DATA_CLIENT, DATA_STORE, DATA_TASK,
    DEFAULT_VERIFY_SSL, DOMAIN, PLATFORMS
)
from .store import ProtectEventStore

async def async_setup_entry(hass, entry):
    client = ProtectApiClient(
        async_get_clientsession(hass),
        entry.data[CONF_HOST],
        entry.data[CONF_API_KEY],
        entry.data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
    )
    await client.async_get_cameras()
    store = ProtectEventStore(hass, entry.entry_id)
    await store.async_load()

    async def handle_event(event):
        store.add(event)

    task = hass.async_create_task(
        client.async_listen(handle_event),
        name=f"{DOMAIN}_{entry.entry_id}_websocket",
    )
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_CLIENT: client, DATA_STORE: store, DATA_TASK: task
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass, entry):
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unloaded:
        return False
    data = hass.data[DOMAIN].pop(entry.entry_id)
    data[DATA_CLIENT].stop()
    task = data[DATA_TASK]
    task.cancel()
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)
    return True
