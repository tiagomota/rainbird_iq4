"""Switch platform for RainBird IQ4."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pyiq4 import Controller
from pyiq4.exceptions import RainbirdAPIError, RainbirdAuthError, RainbirdConnectionError

from .coordinator import RainbirdIQ4Coordinator
from .entity import RainbirdIQ4Entity
from .types import RainbirdIQ4ConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RainbirdIQ4ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RainBird IQ4 switch entities."""
    coordinator = entry.runtime_data.coordinator
    controller = coordinator.controller

    async_add_entities([RainbirdIQ4ForecastDelaySwitch(coordinator, controller)])

    registered: set[int] = set()

    def _add_new_programs() -> None:
        if coordinator.data is None:
            return
        new_programs = [p for p in coordinator.data.programs if p.id not in registered]
        if new_programs:
            registered.update(p.id for p in new_programs)
            async_add_entities([
                RainbirdIQ4ProgramSwitch(
                    coordinator, controller, p.id, p.short_name, p.name
                )
                for p in new_programs
            ])

    _add_new_programs()
    entry.async_on_unload(coordinator.async_add_listener(_add_new_programs))


class RainbirdIQ4ForecastDelaySwitch(RainbirdIQ4Entity, SwitchEntity):
    """Switch to enable/disable forecast-based rain delay."""

    _attr_translation_key = "forecast_delay"
    _attr_icon = "mdi:cloud-percent"

    def __init__(self, coordinator: RainbirdIQ4Coordinator, controller: Controller) -> None:
        super().__init__(coordinator, controller)
        self._attr_unique_id = f"{controller.mac_address}-forecast-delay"

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data
        if data is None or data.rain_delay is None:
            return None
        return data.rain_delay.use_forecast

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set_forecast(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set_forecast(False)

    async def _set_forecast(self, enabled: bool) -> None:
        rain_delay = self.coordinator.data.rain_delay if self.coordinator.data else None
        try:
            await self.coordinator.client.set_forecast_config(
                self._controller.id,
                use_forecast=enabled,
                percent_limit=rain_delay.forecast_percent_limit if rain_delay else 70,
                inches_limit=rain_delay.forecast_inches_limit if rain_delay else 0.5,
                delay_days=rain_delay.forecast_delay_days if rain_delay else 1,
            )
        except (RainbirdAuthError, RainbirdAPIError, RainbirdConnectionError) as err:
            raise HomeAssistantError(f"Failed to update forecast delay: {err}") from err
        await self.coordinator.async_request_refresh()


class RainbirdIQ4ProgramSwitch(RainbirdIQ4Entity, SwitchEntity):
    """Switch to enable/disable an irrigation program."""

    _attr_icon = "mdi:sprinkler-variant"

    def __init__(
        self,
        coordinator: RainbirdIQ4Coordinator,
        controller: Controller,
        program_id: int,
        program_short_name: str,
        program_name: str,
    ) -> None:
        super().__init__(coordinator, controller)
        self._program_id = program_id
        self._attr_unique_id = f"{controller.mac_address}-program-{program_id}"
        self._attr_name = f"Program {program_short_name} - {program_name}"

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        for program in self.coordinator.data.programs:
            if program.id == self._program_id:
                return program.is_enabled
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set_enabled(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set_enabled(False)

    async def _set_enabled(self, enabled: bool) -> None:
        client = self.coordinator.client
        try:
            detail = await client.get_program_detail(self._program_id)
            detail.is_enabled = enabled
            await client.update_program(detail)
        except (RainbirdAuthError, RainbirdAPIError, RainbirdConnectionError) as err:
            raise HomeAssistantError(f"Failed to update program: {err}") from err
        await self.coordinator.async_request_refresh()
