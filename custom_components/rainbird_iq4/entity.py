"""Base entity for RainBird IQ4."""

from __future__ import annotations

from pyiq4 import Controller

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import RainbirdIQ4Coordinator


class RainbirdIQ4Entity(CoordinatorEntity[RainbirdIQ4Coordinator]):
    """Base class for all RainBird IQ4 entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: RainbirdIQ4Coordinator, controller: Controller) -> None:
        super().__init__(coordinator)
        self._controller = controller
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, controller.mac_address)},
            name=f"{controller.name} ({controller.site_name})",
            manufacturer=MANUFACTURER,
            model="IQ4",
            sw_version=controller.version,
        )
