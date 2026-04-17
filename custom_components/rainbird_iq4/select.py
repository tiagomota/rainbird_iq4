"""Select platform for RainBird IQ4."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pyiq4 import Controller
from pyiq4.exceptions import RainbirdAPIError, RainbirdAuthError, RainbirdConnectionError

from .coordinator import RainbirdIQ4Coordinator
from .entity import RainbirdIQ4Entity
from .types import RainbirdIQ4ConfigEntry

# The app displays cm labels but the API stores inches.
# 0.1 in ≈ 0.25 cm, 0.2 in ≈ 0.5 cm, 0.4 in ≈ 1 cm, 0.5 in ≈ 1.25 cm
_RAIN_AMOUNT_CM_TO_INCHES: dict[str, float] = {
    "0.25 cm": 0.1,
    "0.5 cm": 0.2,
    "1 cm": 0.4,
    "1.25 cm": 0.5,
}
_RAIN_AMOUNT_INCHES_TO_CM: dict[float, str] = {
    v: k for k, v in _RAIN_AMOUNT_CM_TO_INCHES.items()
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RainbirdIQ4ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RainBird IQ4 select entities."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities([
        RainbirdIQ4ForecastRainAmountSelect(coordinator, coordinator.controller),
    ])


class RainbirdIQ4ForecastRainAmountSelect(RainbirdIQ4Entity, SelectEntity):
    """Select the rain amount threshold that triggers a forecast delay.

    Options are the four values the IQ4 app exposes, displayed in cm
    (the app's preferred unit) while the API stores inches internally.
    """

    _attr_options = list(_RAIN_AMOUNT_CM_TO_INCHES)
    _attr_translation_key = "forecast_rain_amount"
    _attr_icon = "mdi:weather-rainy"

    def __init__(self, coordinator: RainbirdIQ4Coordinator, controller: Controller) -> None:
        super().__init__(coordinator, controller)
        self._attr_unique_id = f"{controller.mac_address}-forecast-rain-amount"

    @property
    def current_option(self) -> str | None:
        data = self.coordinator.data
        if data is None or data.rain_delay is None:
            return None
        return _RAIN_AMOUNT_INCHES_TO_CM.get(data.rain_delay.forecast_inches_limit)

    async def async_select_option(self, option: str) -> None:
        inches = _RAIN_AMOUNT_CM_TO_INCHES[option]
        rd = self.coordinator.data.rain_delay if self.coordinator.data else None
        try:
            await self.coordinator.client.set_forecast_config(
                self._controller.id,
                use_forecast=rd.use_forecast if rd else False,
                percent_limit=rd.forecast_percent_limit if rd else 70,
                inches_limit=inches,
                delay_days=rd.forecast_delay_days if rd else 1,
            )
        except (RainbirdAuthError, RainbirdAPIError, RainbirdConnectionError) as err:
            raise HomeAssistantError(f"Failed to update rain amount threshold: {err}") from err
        await self.coordinator.async_request_refresh()
