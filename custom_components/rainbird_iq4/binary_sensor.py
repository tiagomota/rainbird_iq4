"""Binary sensor platform for RainBird IQ4."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    """Set up RainBird IQ4 binary sensors."""
    coordinator = entry.runtime_data.coordinator
    controller = coordinator.controller
    async_add_entities([
        RainbirdIQ4ConnectedSensor(coordinator, controller),
        RainbirdIQ4IrrigationActiveSensor(coordinator, controller),
    ])


class RainbirdIQ4ConnectedSensor(RainbirdIQ4Entity, BinarySensorEntity):
    """Binary sensor indicating whether the controller is connected."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_translation_key = "connected"

    def __init__(self, coordinator: RainbirdIQ4Coordinator, controller: Controller) -> None:
        super().__init__(coordinator, controller)
        self._attr_unique_id = f"{controller.mac_address}-connected"

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.is_connected if self.coordinator.data else None


class RainbirdIQ4IrrigationActiveSensor(RainbirdIQ4Entity, BinarySensorEntity):
    """Binary sensor: True when the controller is active, False when turned off."""

    _attr_translation_key = "irrigation_active"
    _attr_icon = "mdi:sprinkler"

    def __init__(self, coordinator: RainbirdIQ4Coordinator, controller: Controller) -> None:
        super().__init__(coordinator, controller)
        self._attr_unique_id = f"{controller.mac_address}-shutdown"

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        return not self.coordinator.data.controller.is_shutdown
