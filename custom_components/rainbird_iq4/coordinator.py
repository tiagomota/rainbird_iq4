"""Data update coordinator for RainBird IQ4."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pyiq4 import (
    Controller,
    Program,
    RainDelayConfig,
    RainbirdIQ4Client,
    authenticate,
)
from pyiq4.exceptions import RainbirdAPIError, RainbirdAuthError, RainbirdConnectionError

from .const import CONF_EMAIL, DOMAIN, UPDATE_INTERVAL_SECONDS

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


@dataclass
class RainbirdIQ4DeviceState:
    """Coordinator data for a single controller."""

    controller: Controller
    is_connected: bool
    programs: list[Program]
    rain_delay: RainDelayConfig | None


class RainbirdIQ4Coordinator(DataUpdateCoordinator[RainbirdIQ4DeviceState]):
    """Coordinator: controller state, connection, programs."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: RainbirdIQ4Client,
        controller: Controller,
        token_lock: asyncio.Lock,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN}_{controller.name}",
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )
        self._client = client
        self._controller = controller
        self._token_lock = token_lock
        self._stale_token: str | None = None

    @property
    def client(self) -> RainbirdIQ4Client:
        return self._client

    @property
    def controller(self) -> Controller:
        return self._controller

    async def _async_update_data(self) -> RainbirdIQ4DeviceState:
        try:
            return await self._fetch_data()
        except RainbirdAuthError:
            if self._client.access_token == self._stale_token:
                raise
            self._stale_token = self._client.access_token
            await self._refresh_token()
            return await self._fetch_data()
        except RainbirdConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
        except RainbirdAPIError as err:
            raise UpdateFailed(f"API error: {err}") from err

    async def _fetch_data(self) -> RainbirdIQ4DeviceState:
        statuses = await self._client.get_connection_status([self._controller.id])
        is_connected = statuses[0].is_connected if statuses else False

        programs = await self._client.get_programs(self._controller.id)
        rain_delay = await self._client.get_rain_delay_config(self._controller.id)

        return RainbirdIQ4DeviceState(
            controller=self._controller,
            is_connected=is_connected,
            programs=programs,
            rain_delay=rain_delay,
        )

    async def _refresh_token(self) -> None:
        async with self._token_lock:
            session = async_get_clientsession(self.hass)
            email = self.config_entry.data[CONF_EMAIL]
            password = self.config_entry.data[CONF_PASSWORD]
            try:
                new_token = await authenticate(session, email, password)
                self._client.update_token(new_token)
                _LOGGER.debug("Token refreshed successfully")
            except RainbirdAuthError as err:
                raise ConfigEntryAuthFailed(
                    "Re-authentication failed — password may have changed"
                ) from err
