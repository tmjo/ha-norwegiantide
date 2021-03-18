"""Switch platform for NorwegianTide."""
import logging

from homeassistant.components.switch import SwitchEntity

from .const import DOMAIN
from .entity import NorwegianTideEntity

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = coordinator.get_switch_entities()
    _LOGGER.debug(
        f"Setting up switch platform for {coordinator.place}, {len(entities)} entities"
    )
    async_add_devices(entities)


class NorwegianTideSwitch(NorwegianTideEntity, SwitchEntity):
    """NorwegianTide switch class."""

    async def async_turn_on(self, **kwargs):  # pylint: disable=unused-argument
        """Turn on the switch."""
        await self.coordinator.api.async_set_title("bar")
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):  # pylint: disable=unused-argument
        """Turn off the switch."""
        await self.coordinator.api.async_set_title("foo")
        await self.coordinator.async_request_refresh()

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self._state
