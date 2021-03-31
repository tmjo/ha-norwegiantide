"""Constants for NorwegianTide."""
from homeassistant.const import DEVICE_CLASS_TIMESTAMP, LENGTH_CENTIMETERS, TIME_HOURS

# Base component constants
NAME = "Norwegian Tide"
DOMAIN = "norwegiantide"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "2021.3.5"
ATTRIBUTION = "Data from ©Kartverket (www.kartverket.no)"
MANUFACTURER = "kartverket.no"
ISSUE_URL = "https://github.com/tmjo/ha-norwegiantide/issues"

# Platforms
BINARY_SENSOR = "binary_sensor"
SENSOR = "sensor"
SWITCH = "switch"
CAMERA = "camera"
PLATFORMS = [BINARY_SENSOR, SENSOR, SWITCH, CAMERA]

# Configuration and options
CONF_ENABLED = "enabled"
CONF_PLACE = "place"
CONF_LAT = "latitude"
CONF_LONG = "longitude"
CONF_STRINGTIME = "%d.%m %H:%M"

# Defaults
STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""

TIDE_EBB = "ebb"
TIDE_FLOW = "flow"
TIDE_LOW = "low"
TIDE_HIGH = "high"
TIDE_STATUS = {
    1: TIDE_EBB,
    2: TIDE_FLOW,
}

ENTITIES = {
    "tide_main": {
        "type": "sensor",
        "key": "currentdata.forecast",
        "attrs": [
            CONF_LAT,
            CONF_LONG,
            "location_details",
            "ebb_flow",
            "ebbing",
            "flowing",
            "tide_state",
            "next_tide",
            "time_to_next_tide",
            "next_tide_low",
            "time_to_next_low",
            "next_tide_high",
            "time_to_next_high",
            "currentdata.prediction",
            "currentdata.forecast",
            "currentdata.observation",
            "currentobservation.weathereffect",
            "data",
        ],
        "units": LENGTH_CENTIMETERS,
        "convert_units_func": None,
        "device_class": None,
        "icon": "mdi:wave",
        "state_func": None,
    },
    "tide_ebbing": {
        "type": "binary_sensor",
        "key": "ebb_flow",
        "attrs": [
            "ebb_flow",
            "time_to_next_tide",
            "next_tide_time",
        ],
        "units": None,
        "convert_units_func": None,
        "device_class": None,
        "icon": "mdi:arrow-expand-down",
        "state_func": lambda ebb_flow: ebb_flow == TIDE_EBB,
    },
    "tide_flowing": {
        "type": "binary_sensor",
        "key": "ebb_flow",
        "attrs": [
            "ebb_flow",
            "time_to_next_tide",
            "next_tide_time",
        ],
        "units": None,
        "convert_units_func": None,
        "device_class": None,
        "icon": "mdi:arrow-expand-up",
        "state_func": lambda ebb_flow: ebb_flow == TIDE_FLOW,
    },
    "tide_ebb_flow": {
        "type": "sensor",
        "key": "ebb_flow",
        "attrs": ["next_tide_time", "time_to_next_tide"],
        "units": None,
        "convert_units_func": None,
        "device_class": "ebb_flow",
        "icon": "mdi:wave",
    },
    "tide_next": {
        "type": "sensor",
        "key": "next_tide.time",
        "attrs": [
            "next_tide",
            "time_to_next_tide",
            "time_to_next_low",
            "time_to_next_high",
            "highlow",
        ],
        "units": None,
        "convert_units_func": "",
        "device_class": None,
        "icon": "mdi:wave",
    },
    "tide_next_low": {
        "type": "sensor",
        "key": "next_tide_low.time",
        "attrs": ["next_tide_low", "time_to_next_low"],
        "units": None,
        "convert_units_func": "",
        "device_class": None,
        "icon": "mdi:wave",
    },
    "tide_next_high": {
        "type": "sensor",
        "key": "next_tide_high.time",
        "attrs": ["next_tide_high", "time_to_next_high"],
        "units": None,
        "convert_units_func": "",
        "device_class": None,
        "icon": "mdi:waves",
    },
    "tide_time_to_next": {
        "type": "sensor",
        "key": "time_to_next_tide",
        "attrs": ["next_tide_time"],
        "units": TIME_HOURS,
        "convert_units_func": "round_2_dec",
        "device_class": None,
        "icon": "mdi:wave",
        "state_func": lambda delta2next: delta2next.total_seconds() / 3600,
    },
    "tide_time_to_next_low": {
        "type": "sensor",
        "key": "time_to_next_low",
        "attrs": ["next_tide_low"],
        "units": TIME_HOURS,
        "convert_units_func": "round_2_dec",
        "device_class": None,
        "icon": "mdi:wave",
        "state_func": lambda delta2next: delta2next.total_seconds() / 3600,
    },
    "tide_time_to_next_high": {
        "type": "sensor",
        "key": "time_to_next_high",
        "attrs": ["next_tide_high"],
        "units": TIME_HOURS,
        "convert_units_func": "round_2_dec",
        "device_class": None,
        "icon": "mdi:waves",
        "state_func": lambda delta2next: delta2next.total_seconds() / 3600,
    },
    "tide_state": {
        "type": "sensor",
        "key": "tide_state",
        "attrs": ["next_tide_time", "time_to_next_tide"],
        "units": None,
        "convert_units_func": None,
        "device_class": "tide_state",
        "icon": "mdi:wave",
    },
    "tide_prediction": {
        "type": "sensor",
        "key": "currentdata.prediction",
        "attrs": [
            "ebb_flow",
            "next_tide_time",
            "time_to_next_tide",
        ],
        "units": LENGTH_CENTIMETERS,
        "convert_units_func": None,
        "device_class": None,
        "icon": "mdi:wave",
    },
    "tide_forecast": {
        "type": "sensor",
        "key": "currentdata.forecast",
        "attrs": [
            "ebb_flow",
            "next_tide_time",
            "time_to_next_tide",
        ],
        "units": LENGTH_CENTIMETERS,
        "convert_units_func": None,
        "device_class": None,
        "icon": "mdi:wave",
    },
    "tide_observation": {
        "type": "sensor",
        "key": "currentobservation.observation",
        "attrs": [
            "ebb_flow",
            "next_tide_time",
            "time_to_next_tide",
        ],
        "units": LENGTH_CENTIMETERS,
        "convert_units_func": None,
        "device_class": None,
        "icon": "mdi:wave",
    },
    "tide_weathereffect": {
        "type": "sensor",
        "key": "currentobservation.weathereffect",
        "attrs": [],
        "units": LENGTH_CENTIMETERS,
        "convert_units_func": None,
        "device_class": None,
        "icon": "mdi:wave",
    },
    "tide_cam": {
        "type": "camera",
        "key": "currentdata.forecast",
        "attrs": [
            "ebb_flow",
            "next_tide_time",
            "time_to_next_tide",
        ],
        "units": None,
        "convert_units_func": None,
        "device_class": None,
        "icon": "mdi:home",
        "state_func": None,
    },
}
