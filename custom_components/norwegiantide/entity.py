"""NorwegianTideEntity class"""
import logging
from datetime import datetime, timedelta
from typing import Callable, List

from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt

from .const import (
    ATTRIBUTION,
    CONF_STRINGTIME,
    DOMAIN,
    MANUFACTURER,
    NAME,
    TIDE_FLOW,
    TIDE_STATUS,
    VERSION,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)


def round_to_dec(value, decimals=None, unit=None):
    """Round to selected no of decimals."""
    try:
        return round(value, decimals)
    except TypeError:
        pass
    return value


def round_2_dec(value, unit=None):
    return round_to_dec(value, 2, unit)


def round_1_dec(value, unit=None):
    return round_to_dec(value, 1, unit)


def round_0_dec(value, unit=None):
    return round_to_dec(value, None, unit)


def map_tide_status(value, unit=None):
    return TIDE_STATUS.get(value, f"unknown {value}")


convert_units_funcs = {
    "round_0_dec": round_0_dec,
    "round_1_dec": round_1_dec,
    "round_2_dec": round_2_dec,
    "map_tide_status": map_tide_status,
}


class NorwegianTideEntity(CoordinatorEntity):
    def __init__(
        self,
        coordinator,
        config_entry,
        place,
        name: str,
        state_key: str,
        units: str,
        convert_units_func: Callable,
        attrs_keys: List[str],
        device_class: str,
        icon: str,
        state_func=None,
        switch_func=None,
    ):
        """Initialize the entity."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._place = place
        self._entity_name = name
        self._state_key = state_key
        self._units = units
        self._convert_units_func = convert_units_func
        self._attrs_keys = attrs_keys
        self._device_class = device_class
        self._icon = icon
        self._state_func = state_func
        self._state = None
        self._switch_func = switch_func

    async def async_added_to_hass(self) -> None:
        """Entity created."""
        await super().async_added_to_hass()
        self.hass.data[DOMAIN]["entities"].append({self._entity_name: self.entity_id})
        self.async_schedule_update_ha_state(force_refresh=True)

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return f"{self._place}_{self._entity_name}"

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._place}_{self._entity_name}".replace("_", " ")

    @property
    def device_info(self):
        """Return the device information."""
        return {
            "identifiers": {(DOMAIN, self._place)},
            "name": f"{NAME} - {self._place}",
            "model": VERSION,
            "manufacturer": MANUFACTURER,
        }

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._units

    @property
    def available(self):
        """Return True if entity is available."""
        return self._state is not None

    @property
    def state_attributes(self):
        """Return the state attributes."""
        attrs = {
            "integration": DOMAIN,
            "attribution": ATTRIBUTION,
        }

        try:
            attrs.update(self.coordinator.data.get("place"))
            for attr_key in self._attrs_keys:
                key = attr_key.replace(".", "_")
                attrs[key] = self.get_value_from_key(attr_key)
            return attrs
        except IndexError:
            _LOGGER.debug(f"Could not find attribute key for {self._entity_name}")
            return attrs

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        try:
            if self._icon == "mdi:wave" and self._state == TIDE_FLOW:
                return "mdi:waves"
        except:
            pass
        return self._icon

    @property
    def device_class(self):
        """Device class of sensor."""
        return self._device_class

    @property
    def should_poll(self):
        """Define if polling needed."""
        return False

    def get_value_from_key(self, key):
        try:
            first, second = key.split(".")
        except ValueError:
            first = key
            second = None

        data = self.coordinator.data.get(first, None)
        if isinstance(data, dict) and second is not None:
            value = data.get(second, None)
            if value is None:
                _LOGGER.debug(f"Did not find data for {first}.{second}")
        elif data is not None:
            value = data
        else:
            value = None
            _LOGGER.debug(f"Did not find data for {first}")

        if type(value) is datetime:
            value = dt.as_local(value)
            # value = value.strftime(CONF_STRINGTIME)
        if type(value) is timedelta:
            # TODO: Dirtyfix to avoid unable to serialize JSON error for timedeltas in attributes, divide on other timedelta gives float
            value = round(value / timedelta(hours=1), 1)
        return value

    async def async_update(self):
        """Get the latest data and update the state."""
        _LOGGER.debug(f"Entity async_update for {self._place} {self._entity_name}")

        self._state = self.get_value_from_key(self._state_key)
        if self._state_func is not None:
            try:
                self._state = self._state_func(
                    self.coordinator.data.get(self._state_key)
                )
            except Exception as e:
                _LOGGER.debug(
                    f"Failed when trying state function {self._state_func}: {e}"
                )
        if self._convert_units_func is not None:
            try:
                self._state = self._convert_units_func(self._state, self._units)
            except Exception as e:
                _LOGGER.debug(
                    f"Failed when trying conversion {self._convert_units_func}: {e}"
                )
