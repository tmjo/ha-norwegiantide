

"""
Custom coordinator for NorwegianTide with Home Assistant.

"""
# import asyncio
# import os
from datetime import timedelta
import logging

from homeassistant.const import CONF_MONITORED_CONDITIONS
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator #, UpdateFailed
from homeassistant.helpers.event import async_track_time_interval
from .entity import convert_units_funcs


from .api import NorwegianTideApiClient
from .entity import convert_units_funcs
from .binary_sensor import NorwegianTideBinarySensor
from .sensor import NorwegianTideSensor
from .switch import NorwegianTideSwitch
from .camera import NorwegianTideCam

from .const import (
    CONF_LAT,
    CONF_LONG,
    CONF_PLACE,
    DOMAIN,
    ENTITIES,
    PLATFORMS,
    STARTUP_MESSAGE,
)

API_SCAN_INTERVAL = timedelta(minutes=5)
ENTITIES_SCAN_INTERVAL = timedelta(seconds=60)

_LOGGER: logging.Logger = logging.getLogger(__package__)


class NorwegianTideDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, client: NorwegianTideApiClient
    ):
        """Initialize."""
        self.api = client
        self.platforms = []
        self.entry = entry  # ??
        self.place = entry.data.get(CONF_PLACE)

        self.sensor_entities = []
        self.switch_entities = []
        self.binary_sensor_entities = []
        self.camera_entities = []

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=API_SCAN_INTERVAL)

    async def _async_update_data(self):
        """Update data via library."""
        _LOGGER.debug(f"Coordinator update.")
        data = await self.api.async_get_data()
        await self.update_ha_state()
        return data

    async def add_schedulers(self):
        """ Add schedules to udpate data """
        _LOGGER.debug(f"Adding schedulers.")
        async_track_time_interval(
            self.hass,
            self.update_ha_state,
            ENTITIES_SCAN_INTERVAL,
        )

    async def update_ha_state(self, now=None):
        # Internal update from API without external calls
        # self.data = self.api.process_data()

        # Schedule an update for all other included entities
        all_entities = (
            self.switch_entities
            + self.sensor_entities
            + self.binary_sensor_entities
            + self.camera_entities
        )
        _LOGGER.debug(f"Update HA state for {len(all_entities)} entities.")
        for entity in all_entities:
            entity.async_schedule_update_ha_state(True)

    def _create_entitites(self):
        _LOGGER.debug(f"Creating entities for {self.place}.")

        # Get monitored conditions if defined in options, otherwise add all
        monitored_conditions = list(
            dict.fromkeys(self.entry.options.get(CONF_MONITORED_CONDITIONS, ENTITIES))
        )

        for key in monitored_conditions:
            if key not in ENTITIES:
                continue
            data = ENTITIES[key]
            entity_type = data.get("type", "sensor")

            _LOGGER.debug(f"Adding {entity_type} entity: {key} for {self.place}")

            if entity_type == "sensor":
                self.sensor_entities.append(
                    NorwegianTideSensor(
                        coordinator=self,
                        config_entry=self.entry,
                        place=self.place,
                        name=key,
                        state_key=data["key"],
                        units=data["units"],
                        convert_units_func=convert_units_funcs.get(
                            data["convert_units_func"], None
                        ),
                        attrs_keys=data["attrs"],
                        device_class=data["device_class"],
                        icon=data["icon"],
                        state_func=data.get("state_func", None),
                    )
                )
            elif entity_type == "switch":
                self.switch_entities.append(
                    NorwegianTideSwitch(
                        coordinator=self,
                        config_entry=self.entry,
                        place=self.place,
                        name=key,
                        state_key=data["key"],
                        units=data["units"],
                        convert_units_func=convert_units_funcs.get(
                            data["convert_units_func"], None
                        ),
                        attrs_keys=data["attrs"],
                        device_class=data["device_class"],
                        icon=data["icon"],
                        state_func=data.get("state_func", None),
                        switch_func=data.get("switch_func", None),
                    )
                )
            elif entity_type == "binary_sensor":
                self.binary_sensor_entities.append(
                    NorwegianTideBinarySensor(
                        coordinator=self,
                        config_entry=self.entry,
                        place=self.place,
                        name=key,
                        state_key=data["key"],
                        units=data["units"],
                        convert_units_func=convert_units_funcs.get(
                            data["convert_units_func"], None
                        ),
                        attrs_keys=data["attrs"],
                        device_class=data["device_class"],
                        icon=data["icon"],
                        state_func=data.get("state_func", None),
                    )
                )
            elif entity_type == "camera":
                self.camera_entities.append(
                    NorwegianTideCam(
                        coordinator=self,
                        config_entry=self.entry,
                        place=self.place,
                        name=key,
                        state_key=data["key"],
                        units=data["units"],
                        convert_units_func=convert_units_funcs.get(
                            data["convert_units_func"], None
                        ),
                        attrs_keys=data["attrs"],
                        device_class=data["device_class"],
                        icon=data["icon"],
                        state_func=data.get("state_func", None),
                    )
                )

    def get_binary_sensor_entities(self):
        return self.binary_sensor_entities

    def get_sensor_entities(self):
        return self.sensor_entities

    def get_switch_entities(self):
        return self.switch_entities

    def get_camera_entities(self):
        return self.camera_entities
