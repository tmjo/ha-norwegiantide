"""
Custom integration to integrate NorwegianTide with Home Assistant.

"""
import asyncio
from homeassistant.const import CONF_MONITORED_CONDITIONS
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.event import async_track_time_interval
from .entity import convert_units_funcs
from .api import NorwegianTideApiClient
from .binary_sensor import NorwegianTideBinarySensor
from .switch import NorwegianTideSwitch
from .sensor import NorwegianTideSensor
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


async def async_setup(hass: HomeAssistant, config: Config):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    latitude = entry.data.get(CONF_LAT)
    longitude = entry.data.get(CONF_LONG)
    place = entry.data.get(CONF_PLACE)

    session = async_get_clientsession(hass)
    client = NorwegianTideApiClient(place, latitude, longitude, session)

    coordinator = NorwegianTideDataUpdateCoordinator(hass, entry=entry, client=client)
    await coordinator.async_refresh()
    coordinator._create_entitites()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    # hass.data[DOMAIN]["coordinator"] = coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator
    hass.data[DOMAIN]["entities"] = []

    for platform in PLATFORMS:
        if entry.options.get(platform, True):
            coordinator.platforms.append(platform)
            hass.async_add_job(
                hass.config_entries.async_forward_entry_setup(entry, platform)
            )

    entry.add_update_listener(async_reload_entry)
    await coordinator.add_schedulers()
    return True


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

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=API_SCAN_INTERVAL)

    async def _async_update_data(self):
        """Update data via library."""
        _LOGGER.debug(f"Coordinator update.")
        # try:
        #     data = await self.api.async_get_data()
        #     self.update_ha_state()
        #     return data
        # except Exception as exception:
        #     _LOGGER.debug(f"Exception while getting data.")
        #     raise UpdateFailed() from exception

        data = await self.api.async_get_data()
        self.update_ha_state()
        return data

    async def add_schedulers(self):
        """ Add schedules to udpate data """
        _LOGGER.debug(f"Adding schedulers.")
        async_track_time_interval(
            self.hass,
            self.update_ha_state,
            ENTITIES_SCAN_INTERVAL,
        )

    def update_ha_state(self, now=None):
        # Internal update from API without external calls
        self.data = self.api.process_data()

        # Schedule an update for all other included entities
        all_entities = (
            self.switch_entities + self.sensor_entities + self.binary_sensor_entities
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
            # for key in ENTITIES:
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

    def get_binary_sensor_entities(self):
        return self.binary_sensor_entities

    def get_sensor_entities(self):
        return self.sensor_entities

    def get_switch_entities(self):
        return self.switch_entities


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.debug(f"Unloading {DOMAIN}: {coordinator.place}")
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
                if platform in coordinator.platforms
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.debug(f"Reloading {DOMAIN}: {coordinator.place}")
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
