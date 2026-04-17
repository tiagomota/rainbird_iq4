"""Sensor platform for RainBird IQ4."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pyiq4 import Controller

from .coordinator import RainbirdIQ4Coordinator
from .entity import RainbirdIQ4Entity
from .types import RainbirdIQ4ConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RainbirdIQ4ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RainBird IQ4 sensors."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities([
        RainbirdIQ4RainDelaySensor(coordinator, coordinator.controller),
    ])


class RainbirdIQ4RainDelaySensor(RainbirdIQ4Entity, SensorEntity):
    """Sensor showing the current rain delay in days."""

    _attr_native_unit_of_measurement = UnitOfTime.DAYS
    _attr_translation_key = "rain_delay"
    _attr_icon = "mdi:water-off"

    def __init__(self, coordinator: RainbirdIQ4Coordinator, controller: Controller) -> None:
        super().__init__(coordinator, controller)
        self._attr_unique_id = f"{controller.mac_address}-rain-delay"

    @property
    def native_value(self) -> int | None:
        data = self.coordinator.data
        if data is None:
            return None
        if data.rain_delay is not None:
            return data.rain_delay.rain_delay_days
        return data.controller.rain_delay
