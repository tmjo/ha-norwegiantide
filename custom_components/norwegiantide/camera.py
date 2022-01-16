"""Camera platform for NorwegianTide."""

from __future__ import annotations
import logging
from datetime import timedelta
import io
from typing import Callable, List
import mimetypes
import os

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
    CONST_DIR_DEFAULT,
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

        # Directories
        # CONST_DIR_THIS = os.path.split(__file__)[0]
        # CONST_DIR_DEFAULT = os.path.join(CONST_DIR_THIS, "tmp")
        # file_path = os.path.join(CONST_DIR_DEFAULT, "norwegianweather.png")
        file_path = os.path.join(CONST_DIR_DEFAULT, self.coordinator.api.file_image)

        self._name = name
        self.check_file_path_access(file_path)
        self._file_path = file_path
        # Set content type of local file
        content, _ = mimetypes.guess_type(file_path)
        if content is not None:
            self.content_type = content

    @property
    def brand(self):
        """Return the camera brand."""
        return self.device_info.get("manufacturer", None)

    @property
    def model(self):
        """Return the camera model."""
        return self.device_info.get("model", None)

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
        # def camera_image(self) -> bytes | None:

        """Return image response."""

        _LOGGER.debug("Updating camera image")
        try:
            with open(self._file_path, "rb") as file:
                return file.read()
        except FileNotFoundError:
            _LOGGER.warning(
                "Could not read camera %s image from file: %s",
                self._name,
                self._file_path,
            )
        return None

    def check_file_path_access(self, file_path):
        """Check that filepath given is readable."""
        if not os.access(file_path, os.R_OK):
            _LOGGER.warning(
                "Could not read camera %s image from file: %s", self._name, file_path
            )

    def update_file_path(self, file_path):
        """Update the file_path."""
        self.check_file_path_access(file_path)
        self._file_path = file_path
        self.schedule_update_ha_state()

    # @property
    # def name(self):
    #     """Return the name of this camera."""
    #     # return self._name
    #     return f"{self._place}_{self._entity_name}".replace("_", " ")

    @property
    def extra_state_attributes(self):
        """Return the camera state attributes."""
        return {"file_path": self._file_path}
