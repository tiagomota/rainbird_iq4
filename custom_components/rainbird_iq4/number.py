"""Number platform for RainBird IQ4."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pyiq4 import Controller, RainDelayConfig
from pyiq4.exceptions import RainbirdAPIError, RainbirdAuthError, RainbirdConnectionError

from .coordinator import RainbirdIQ4Coordinator
from .entity import RainbirdIQ4Entity
from .types import RainbirdIQ4ConfigEntry

_FORECAST_ERRORS = (RainbirdAuthError, RainbirdAPIError, RainbirdConnectionError)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RainbirdIQ4ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RainBird IQ4 number entities."""
    coordinator = entry.runtime_data.coordinator
    controller = coordinator.controller

    async_add_entities([
        RainbirdIQ4RainDelayNumber(coordinator, controller),
        RainbirdIQ4ForecastProbabilityNumber(coordinator, controller),
        RainbirdIQ4ForecastDelayDaysNumber(coordinator, controller),
    ])

    registered: set[int] = set()

    def _add_new_programs() -> None:
        if coordinator.data is None:
            return
        new_programs = [p for p in coordinator.data.programs if p.id not in registered]
        if new_programs:
            registered.update(p.id for p in new_programs)
            async_add_entities([
                RainbirdIQ4SeasonalAdjustmentNumber(
                    coordinator, controller, p.id, p.short_name, p.name
                )
                for p in new_programs
            ])

    _add_new_programs()
    entry.async_on_unload(coordinator.async_add_listener(_add_new_programs))


class RainbirdIQ4RainDelayNumber(RainbirdIQ4Entity, NumberEntity):
    """Number entity to set a manual rain delay (0 = cancel, 1–14 = days)."""

    _attr_native_min_value = 0
    _attr_native_max_value = 14
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.DAYS
    _attr_translation_key = "rain_delay"
    _attr_icon = "mdi:weather-rainy"

    def __init__(self, coordinator: RainbirdIQ4Coordinator, controller: Controller) -> None:
        super().__init__(coordinator, controller)
        self._attr_unique_id = f"{controller.mac_address}-rain-delay-set"

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data
        if data is None or data.rain_delay is None:
            return None
        return float(data.rain_delay.rain_delay_days)

    async def async_set_native_value(self, value: float) -> None:
        try:
            await self.coordinator.client.set_rain_delay(
                self._controller.id, delay_days=int(value)
            )
        except (RainbirdAuthError, RainbirdAPIError, RainbirdConnectionError) as err:
            raise HomeAssistantError(f"Failed to set rain delay: {err}") from err
        await self.coordinator.async_request_refresh()


class _ForecastParamNumber(RainbirdIQ4Entity, NumberEntity):
    """Base for forecast parameter numbers.

    Subclasses override ``native_value`` and ``async_set_native_value``.
    All three forecast params are always written together; subclasses call
    ``_write_forecast`` with the field they own changed and the rest preserved.
    """

    def _rain_delay(self) -> RainDelayConfig | None:
        data = self.coordinator.data
        return data.rain_delay if data else None

    async def _write_forecast(
        self,
        percent_limit: int,
        inches_limit: float,
        delay_days: int,
    ) -> None:
        rd = self._rain_delay()
        try:
            await self.coordinator.client.set_forecast_config(
                self._controller.id,
                use_forecast=rd.use_forecast if rd else False,
                percent_limit=percent_limit,
                inches_limit=inches_limit,
                delay_days=delay_days,
            )
        except _FORECAST_ERRORS as err:
            raise HomeAssistantError(f"Failed to update forecast settings: {err}") from err
        await self.coordinator.async_request_refresh()


class RainbirdIQ4ForecastProbabilityNumber(_ForecastParamNumber):
    """Rain probability threshold that triggers a forecast delay (%)."""

    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 5
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_translation_key = "forecast_probability"
    _attr_icon = "mdi:weather-pouring"

    def __init__(self, coordinator: RainbirdIQ4Coordinator, controller: Controller) -> None:
        super().__init__(coordinator, controller)
        self._attr_unique_id = f"{controller.mac_address}-forecast-probability"

    @property
    def native_value(self) -> float | None:
        rd = self._rain_delay()
        return float(rd.forecast_percent_limit) if rd else None

    async def async_set_native_value(self, value: float) -> None:
        rd = self._rain_delay()
        await self._write_forecast(
            percent_limit=int(value),
            inches_limit=rd.forecast_inches_limit if rd else 0.5,
            delay_days=rd.forecast_delay_days if rd else 1,
        )



class RainbirdIQ4ForecastDelayDaysNumber(_ForecastParamNumber):
    """Number of days to skip irrigation when forecast rain is predicted."""

    _attr_native_min_value = 1
    _attr_native_max_value = 14
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.DAYS
    _attr_translation_key = "forecast_delay_days"
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator: RainbirdIQ4Coordinator, controller: Controller) -> None:
        super().__init__(coordinator, controller)
        self._attr_unique_id = f"{controller.mac_address}-forecast-delay-days"

    @property
    def native_value(self) -> float | None:
        rd = self._rain_delay()
        return float(rd.forecast_delay_days) if rd else None

    async def async_set_native_value(self, value: float) -> None:
        rd = self._rain_delay()
        await self._write_forecast(
            percent_limit=rd.forecast_percent_limit if rd else 70,
            inches_limit=rd.forecast_inches_limit if rd else 0.5,
            delay_days=int(value),
        )


class RainbirdIQ4SeasonalAdjustmentNumber(RainbirdIQ4Entity, NumberEntity):
    """Number entity for program seasonal adjustment percentage."""

    _attr_native_min_value = 0
    _attr_native_max_value = 300
    _attr_native_step = 5
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:percent"

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
        self._attr_unique_id = f"{controller.mac_address}-seasonal-adj-{program_id}"
        self._attr_name = f"Program {program_short_name} - {program_name} seasonal adjustment"

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        for program in self.coordinator.data.programs:
            if program.id == self._program_id:
                return float(program.seasonal_adjustment)
        return None

    async def async_set_native_value(self, value: float) -> None:
        client = self.coordinator.client
        try:
            detail = await client.get_program_detail(self._program_id)
            detail.seasonal_adjustment = int(value)
            await client.update_program(detail)
        except (RainbirdAuthError, RainbirdAPIError, RainbirdConnectionError) as err:
            raise HomeAssistantError(
                f"Failed to update seasonal adjustment: {err}"
            ) from err
        await self.coordinator.async_request_refresh()
