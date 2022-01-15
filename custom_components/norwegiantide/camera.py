"""Camera platform for NorwegianTide."""

from __future__ import annotations
import logging
from datetime import timedelta
import io
from typing import Callable, List

import voluptuous as vol

from homeassistant.components.camera import Camera
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
import homeassistant.helpers.config_validation as cv

from .entity import NorwegianTideEntity

_LOGGER: logging.Logger = logging.getLogger(__package__)

from .const import (
    CONF_STRINGTIME,
    DOMAIN,
    DOMAIN,
    MANUFACTURER,
    NAME,
    VERSION,
    ATTRIBUTION,
)


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = coordinator.get_camera_entities()
    _LOGGER.debug(
        f"Setting up camera platform for {coordinator.place}, {len(entities)} entities"
    )
    async_add_devices(entities)


class NorwegianTideCam(Camera, NorwegianTideEntity):
    """NorwegianTide Camera class."""

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
        NorwegianTideEntity.__init__(
            self,
            coordinator,
            config_entry,
            place,
            name,
            state_key,
            units,
            convert_units_func,
            attrs_keys,
            device_class,
            icon,
            state_func,
            switch_func,
        )
        Camera.__init__(self)

    @property
    def frame_interval(self):
        # this is how often the image will update in the background.
        # When the GUI panel is up, it is always updated every
        # 10 seconds, which is too much. Must figure out how to
        # reduce...
        return 60

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        # def camera_image(self):
        """Load image bytes in memory"""
        # # don't use throttle because extra calls return Nones
        # if not self._loaded:
        #     _LOGGER.debug("Loading image data")
        #     self.sky.load(self._tmpdir)
        #     self._loaded = True
        _LOGGER.debug("Updating camera image")
        try:
            buf = io.BytesIO()
            # self.sky.plot_sky(buf)
            self.coordinator.api.plot_tidedata(buf)
            buf.seek(0)
            return buf.getvalue()
        except:
            _LOGGER.warning("Could not read camera!")
            return None
