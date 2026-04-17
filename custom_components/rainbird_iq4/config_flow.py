"""Config flow for RainBird IQ4."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pyiq4 import Controller, RainbirdIQ4Client, authenticate
from pyiq4.exceptions import RainbirdAuthError, RainbirdConnectionError

from .const import CONF_CONTROLLER_ID, CONF_EMAIL, DOMAIN

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

REAUTH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PASSWORD): str,
    }
)


class RainbirdIQ4ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for RainBird IQ4."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._email: str | None = None
        self._password: str | None = None
        self._controllers: list[Controller] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial setup step — collect credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._email = user_input[CONF_EMAIL]
            self._password = user_input[CONF_PASSWORD]

            try:
                session = async_get_clientsession(self.hass)
                token = await authenticate(session, self._email, self._password)
                client = RainbirdIQ4Client(session, token)
                self._controllers = await client.get_controllers()
            except RainbirdAuthError:
                errors["base"] = "invalid_auth"
            except RainbirdConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during setup")
                errors["base"] = "unknown"
            else:
                if not self._controllers:
                    errors["base"] = "no_controllers"
                elif len(self._controllers) == 1:
                    # Single controller — skip selection step
                    return await self._create_entry(self._controllers[0])
                else:
                    return await self.async_step_select_controller()

        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
        )

    async def async_step_select_controller(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle controller selection step."""
        if user_input is not None:
            controller_id = int(user_input[CONF_CONTROLLER_ID])
            controller = next(c for c in self._controllers if c.id == controller_id)
            return await self._create_entry(controller)

        controller_options = {
            str(c.id): f"{c.name} ({c.site_name})" for c in self._controllers
        }

        return self.async_show_form(
            step_id="select_controller",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CONTROLLER_ID): vol.In(controller_options),
                }
            ),
        )

    async def _create_entry(self, controller: Controller) -> ConfigFlowResult:
        """Create a config entry for a single controller."""
        await self.async_set_unique_id(controller.mac_address)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=f"{controller.name} ({controller.site_name})",
            data={
                CONF_EMAIL: self._email,
                CONF_PASSWORD: self._password,
                CONF_CONTROLLER_ID: controller.id,
            },
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauth triggered by expired/invalid credentials."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the reauth confirmation step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            reauth_entry = self._get_reauth_entry()
            email = reauth_entry.data[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]

            try:
                session = async_get_clientsession(self.hass)
                await authenticate(session, email, password)
            except RainbirdAuthError:
                errors["base"] = "invalid_auth"
            except RainbirdConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during reauth")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data={**reauth_entry.data, CONF_PASSWORD: password},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=REAUTH_SCHEMA,
            errors=errors,
        )
