"""
Custom integration to integrate NorwegianTide with Home Assistant.

"""
import asyncio

# from config.custom_components import norwegiantide
import logging
# from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
# from homeassistant.const import CONF_MONITORED_CONDITIONS
# from homeassistant.core import Config, HomeAssistant
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
# from homeassistant.helpers.event import async_track_time_interval
# from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import NorwegianTideApiClient
from .coordinator import NorwegianTideDataUpdateCoordinator
# from .entity import convert_units_funcs
# from .binary_sensor import NorwegianTideBinarySensor
# from .sensor import NorwegianTideSensor
# from .switch import NorwegianTideSwitch
# from .camera import NorwegianTideCam

# from config.custom_components.norwegiantide.camera import NorwegianTideCam
from .const import (
    CONF_LAT,
    CONF_LONG,
    CONF_PLACE,
    DOMAIN,
    ENTITIES,
    PLATFORMS,
    STARTUP_MESSAGE,
)


# API_SCAN_INTERVAL = timedelta(minutes=5)
# ENTITIES_SCAN_INTERVAL = timedelta(seconds=60)

_LOGGER: logging.Logger = logging.getLogger(__package__)


# async def async_setup(hass: HomeAssistant, config: Config):
async def async_setup(hass: HomeAssistant, config: ConfigType):
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
    # await coordinator.async_refresh()
    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    coordinator._create_entitites()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = coordinator
    hass.data[DOMAIN]["entities"] = []

    # for platform in PLATFORMS:
    #     if entry.options.get(platform, True):
    #         coordinator.platforms.append(platform)
    #         hass.async_add_job(
    #             hass.config_entries.async_forward_entry_setup(entry, platform)
    #         )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    # entry.add_update_listener(async_reload_entry)
    await coordinator.add_schedulers()
    return True



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
