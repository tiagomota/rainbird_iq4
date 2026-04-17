"""RainBird IQ4 integration for Home Assistant."""

from __future__ import annotations

import asyncio

from homeassistant.const import CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pyiq4 import RainbirdIQ4Client, authenticate
from pyiq4.exceptions import RainbirdAuthError, RainbirdConnectionError

from .const import CONF_CONTROLLER_ID, CONF_EMAIL
from .coordinator import RainbirdIQ4Coordinator
from .types import RainbirdIQ4ConfigEntry, RainbirdIQ4Data

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: RainbirdIQ4ConfigEntry) -> bool:
    """Set up RainBird IQ4 from a config entry."""
    session = async_get_clientsession(hass)
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]
    controller_id = entry.data[CONF_CONTROLLER_ID]

    try:
        token = await authenticate(session, email, password)
    except RainbirdAuthError as err:
        raise ConfigEntryAuthFailed("Authentication failed") from err
    except RainbirdConnectionError as err:
        raise ConfigEntryNotReady("Cannot connect to RainBird IQ4 cloud") from err

    client = RainbirdIQ4Client(session, token)

    try:
        controllers = await client.get_controllers()
    except RainbirdConnectionError as err:
        raise ConfigEntryNotReady("Cannot fetch controllers") from err

    controller = next((c for c in controllers if c.id == controller_id), None)
    if controller is None:
        raise ConfigEntryNotReady(f"Controller {controller_id} not found in account")

    coordinator = RainbirdIQ4Coordinator(hass, entry, client, controller, asyncio.Lock())
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = RainbirdIQ4Data(client=client, coordinator=coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: RainbirdIQ4ConfigEntry) -> bool:
    """Unload a RainBird IQ4 config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
