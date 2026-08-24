import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_HOST
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import BooleanSelector

from .api import ProtectApiClient, ProtectApiError, ProtectAuthError, ProtectConnectionError
from .const import CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL, DOMAIN

class UniFiProtectEventsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip().rstrip("/")
            await self.async_set_unique_id(host.lower())
            self._abort_if_unique_id_configured()
            client = ProtectApiClient(
                async_get_clientsession(self.hass),
                host,
                user_input[CONF_API_KEY],
                user_input[CONF_VERIFY_SSL],
            )
            try:
                cameras = await client.async_get_cameras()
            except ProtectAuthError:
                errors["base"] = "invalid_auth"
            except ProtectConnectionError:
                errors["base"] = "cannot_connect"
            except ProtectApiError:
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"UniFi Protect Events ({len(cameras)} camera's)",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default="unifi-console.local"): str,
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): BooleanSelector(),
            }),
            errors=errors,
        )
