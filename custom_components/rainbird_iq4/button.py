"""Button platform for RainBird IQ4."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pyiq4 import Controller
from pyiq4.exceptions import RainbirdAPIError, RainbirdAuthError, RainbirdConnectionError

from .coordinator import RainbirdIQ4Coordinator
from .entity import RainbirdIQ4Entity
from .types import RainbirdIQ4ConfigEntry

_ERRORS = (RainbirdAuthError, RainbirdAPIError, RainbirdConnectionError)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RainbirdIQ4ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RainBird IQ4 button entities."""
    coordinator = entry.runtime_data.coordinator
    controller = coordinator.controller

    async_add_entities([RainbirdIQ4StopAllIrrigationButton(coordinator, controller)])

    registered: set[int] = set()

    def _add_new_programs() -> None:
        if coordinator.data is None:
            return
        new_programs = [p for p in coordinator.data.programs if p.id not in registered]
        if new_programs:
            registered.update(p.id for p in new_programs)
            async_add_entities([
                RainbirdIQ4RunProgramButton(
                    coordinator, controller, p.id, p.short_name, p.name
                )
                for p in new_programs
            ])

    _add_new_programs()
    entry.async_on_unload(coordinator.async_add_listener(_add_new_programs))


class RainbirdIQ4StopAllIrrigationButton(RainbirdIQ4Entity, ButtonEntity):
    """Button that immediately stops all running irrigation."""

    _attr_translation_key = "stop_all_irrigation"
    _attr_icon = "mdi:stop-circle-outline"

    def __init__(self, coordinator: RainbirdIQ4Coordinator, controller: Controller) -> None:
        super().__init__(coordinator, controller)
        self._attr_unique_id = f"{controller.mac_address}-stop-all"

    async def async_press(self) -> None:
        try:
            await self.coordinator.client.stop_all_irrigation(self._controller.id)
        except _ERRORS as err:
            raise HomeAssistantError(f"Failed to stop irrigation: {err}") from err
        await self.coordinator.async_request_refresh()


class RainbirdIQ4RunProgramButton(RainbirdIQ4Entity, ButtonEntity):
    """Button that starts a program immediately (manual run)."""

    _attr_icon = "mdi:play-circle-outline"

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
        self._attr_unique_id = f"{controller.mac_address}-run-program-{program_id}"
        self._attr_name = f"Program {program_short_name} - {program_name} run now"

    async def async_press(self) -> None:
        try:
            await self.coordinator.client.start_program(self._program_id)
        except _ERRORS as err:
            raise HomeAssistantError(f"Failed to start program: {err}") from err
        await self.coordinator.async_request_refresh()
