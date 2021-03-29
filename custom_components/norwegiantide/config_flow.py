"""Adds config flow for NorwegianTide."""
import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_MONITORED_CONDITIONS
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import NorwegianTideApiClient
from .const import CONF_LAT, CONF_LONG, CONF_PLACE, DOMAIN, ENTITIES, PLATFORMS

_LOGGER: logging.Logger = logging.getLogger(__package__)


class NorwegianTideFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for NorwegianTide."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        # Uncomment the next 2 lines if only a single instance of the integration is allowed:
        # if self._async_current_entries():
        #     return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            valid = await self._test_credentials(
                user_input[CONF_PLACE],
                user_input[CONF_LAT],
                user_input[CONF_LONG],
            )
            if valid:
                entry = self.async_create_entry(
                    title=user_input[CONF_PLACE], data=user_input
                )
                _LOGGER.debug(f"ConfigEntry: {entry}")
                return entry
            else:
                self._errors["base"] = "auth"

            return await self._show_config_form(user_input)

        return await self._show_config_form(user_input)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        entity_multi_select = {x: x for x in list(ENTITIES)}
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_PLACE, default=self.hass.config.location_name
                    ): str,
                    vol.Required(
                        CONF_LAT, default=self.hass.config.latitude
                    ): vol.Coerce(float),
                    vol.Required(
                        CONF_LONG, default=self.hass.config.longitude
                    ): vol.Coerce(float),
                    vol.Optional(
                        CONF_MONITORED_CONDITIONS,
                        default=list(ENTITIES),
                    ): cv.multi_select(entity_multi_select),
                }
            ),
            errors=self._errors,
        )

    async def _test_credentials(self, place, latitude, longitude):
        """Return true if credentials is valid."""
        try:
            session = async_create_clientsession(self.hass)
            client = NorwegianTideApiClient(place, latitude, longitude, session)
            await client.async_get_data()
            return True
        except Exception:  # pylint: disable=broad-except
            pass
        return False

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return NorwegianTideOptionsFlowHandler(config_entry)


class NorwegianTideOptionsFlowHandler(config_entries.OptionsFlow):
    """NorwegianTide config flow options handler."""

    def __init__(self, config_entry):
        """Initialize HACS options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):
        """Manage the options."""

        errors = {}
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        entity_multi_select = {x: x for x in list(ENTITIES)}
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_MONITORED_CONDITIONS,
                        default=self.config_entry.options.get(
                            CONF_MONITORED_CONDITIONS, list(ENTITIES)
                        ),
                    ): cv.multi_select(entity_multi_select),
                }
            ),
            errors=errors,
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(
            title=self.config_entry.data.get(CONF_PLACE), data=self.options
        )
