"""Sample API Client."""
from datetime import timedelta
import logging
import asyncio
import socket
from typing import Optional
import aiohttp
import async_timeout
import xml.etree.ElementTree as ET
import re
from homeassistant.util import dt
from decimal import Decimal
from .const import TIDE_EBB, TIDE_FLOW

TIMEOUT = 30  # seconds
API_PREDICTION = "prediction"
API_OBSERVATION = "observation"
API_FORECAST = "forecast"
API_STRINGTIME = "%Y-%m-%dT%H:%M:%S.%f%z"
API_LANG = "nb"
API_LOW = "low"
API_HIGH = "high"

_LOGGER: logging.Logger = logging.getLogger(__package__)

HEADERS = {"Content-type": "application/json; charset=UTF-8"}


class NorwegianTideApiClient:
    def __init__(
        self, place, latitude, longitude, session: aiohttp.ClientSession
    ) -> None:

        """Sample API Client."""
        self._session = session
        self.place = place
        self.lat = latitude
        self.lon = longitude

        self.highlow = []
        self.location = {}
        self.tidedata = {}
        self.tidedatatime = {}
        self.next_tide = {}

    def get_url(
        self,
        datatype="all",
        refcode="cd",
        lang=API_LANG,
        interval=10,
        fromtime=None,
        totime=None,
    ):
        if fromtime is None:
            fromtime = dt.now() - timedelta(hours=12)

        if totime is None:
            totime = fromtime + timedelta(hours=36)

        fromtime = fromtime.strftime(API_STRINGTIME)
        totime = totime.strftime(API_STRINGTIME)
        url = f"http://api.sehavniva.no/tideapi.php?lat={self.lat}&lon={self.lon}&fromtime={fromtime}&totime={totime}&datatype={datatype}&refcode={refcode}&place={self.place}&file=&lang={lang}&interval={interval}&dst=0&tzone=&tide_request=locationdata"
        return url

    async def async_get_data(self) -> dict:
        """Get data from the API."""
        _LOGGER.debug("Calling API to fetch new data")

        # Get XML
        await self.get_xml_data()

        # Process data
        self.location = self.process_location()
        self.tidedatatime = self.process_tidedatatime()
        self.highlow = self.process_high_low()
        return self.process_data()

    async def get_xml_data(self):
        try:
            # Get low/high tides table
            response = await self.api_wrapper("get", self.get_url(datatype="tab"))
            content = await response.text()
            self.highlowdata = self.xml_high_low(content)

            # Get prediction, observation and forecast
            response = await self.api_wrapper("get", self.get_url(datatype="all"))
            content = await response.text()
            self.locationdata = self.xml_location(content)
            self.tidedata = self.xml_tidedata(content)
        except AttributeError as exception:
            _LOGGER.debug(
                f"Unable to decode xml possibly due to previous error getting data. {exception}"
            )

    def process_data(self):
        # Process detail data
        self.next_tide = self.getNextTide()
        self.next_tide_low = self.getNextTide(highlow=API_LOW)
        self.next_tide_high = self.getNextTide(highlow=API_HIGH)
        self.time_to_next_tide = self.getTimeToNextTide(self.next_tide)
        self.time_to_next_low = self.getTimeToNextTide(highlow=API_LOW)
        self.time_to_next_high = self.getTimeToNextTide(highlow=API_HIGH)
        self.ebb_flow = self.getTideStateEbbFlow(self.next_tide)
        self.tide_state = self.getTideState(self.next_tide)
        self.tide_state_full = self.getTideStateFull(self.next_tide)
        self.last_data = self.getLastData()
        self.current_data = self.getCurrentData()
        self.current_observation = self.getCurrentDataObservation()
        # self.forecast = self.getData(type=API_FORECAST)
        # self.prediction = self.getData(type=API_PREDICTION)
        # self.observation = self.getData(type=API_OBSERVATION)
        self.data = self.getDataAll()

        return {
            # "location": self.location,
            "location": self.getLocationData(),
            "location_full": self.getLocationData(compact=False),
            "next_tide": self.next_tide,
            "next_tide_time": {self.next_tide.get("time", None)},
            "next_tide_low": self.next_tide_low,
            "next_tide_high": self.next_tide_high,
            "time_to_next_tide": self.time_to_next_tide,
            "time_to_next_low": self.time_to_next_low,
            "time_to_next_high": self.time_to_next_high,
            "ebb_flow": self.ebb_flow,
            "ebbing": self.ebb_flow == TIDE_EBB,
            "flowing": self.ebb_flow == TIDE_FLOW,
            "tide_state": self.tide_state_full,
            # "tide_state": self.tide_state,
            # "tide_state_full": self.tide_state_full,
            "highlow": self.highlow,
            "tidedatatime": self.tidedatatime,
            "tidedata": self.tidedata,
            "lastdata": self.last_data,
            "currentdata": self.current_data,
            "currentobservation": self.current_observation,
            # "forecast": self.forecast,
            # "prediction": self.prediction,
            # "observation": self.observation,
            "data": self.data,
        }

    async def api_wrapper(
        self, method: str, url: str, data: dict = {}, headers: dict = {}
    ):
        """Get information from the API."""
        try:
            async with async_timeout.timeout(TIMEOUT, loop=asyncio.get_event_loop()):
                if method == "get":
                    response = await self._session.get(url, headers=headers)
                    _LOGGER.debug(f"Response: {response.status} from URL: {url}")
                    return response

        except asyncio.TimeoutError as exception:
            _LOGGER.error(f"Timeout fetching information from API")
            _LOGGER.debug(f"Timeout ({exception}) fetching from url {url}")
        except (KeyError, TypeError) as exception:
            _LOGGER.error(f"Error parsing information from API.")
            _LOGGER.debug(f"Error ({exception}) parsing from url {url}")
        except (aiohttp.ClientError, socket.gaierror) as exception:
            _LOGGER.error(f"Error fetching information from API.")
            _LOGGER.debug(f"Error ({exception}) fetching from url {url}")
        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error(f"Something really wrong happend! ({exception}).")

    def xml_location(self, content):
        """Treat XML data for location."""
        location = {}
        root = ET.fromstring(content)
        for locdata in root.iter("location"):
            for attr in locdata.attrib:
                location[attr] = locdata.attrib.get(attr)
                _LOGGER.debug(f"xml_location {attr}: {locdata.attrib.get(attr)}")
        return location

    def xml_high_low(self, content):
        """Treat XML data for high and low tides."""
        highlow = []
        root = ET.fromstring(content)
        for datatype in root.iter("data"):
            for data in datatype.iter("waterlevel"):
                highlow.append(data.attrib)
                _LOGGER.debug(f"xml_high_low: {data.attrib}")
        return highlow

    def xml_tidedata(self, content):
        """Treat XML data for detailed tide information."""
        tidedata = {}
        root = ET.fromstring(content)
        for datatype in root.iter("data"):
            tidedata[datatype.attrib.get("type")] = []
            for data in datatype.iter("waterlevel"):
                tidedata[datatype.attrib.get("type")].append(data.attrib)
        _LOGGER.debug(f"xml_tidedata: {len(tidedata)}")
        return tidedata

    def process_location(self, locationdata=None):
        """Process data for location."""
        location = {}
        if locationdata is None:
            locationdata = self.locationdata

        # <location name="Stavanger"
        # code="SVG"
        # latitude="58.974339"
        # longitude="5.730121"
        # delay="0"
        # factor="1.00"
        # obsname="Stavanger"
        # obscode="SVG"
        # place="Syrevågen"
        # descr="Tidvatn og observert vasstand frå Stavanger"/>
        # <reflevelcode>CD</reflevelcode>

        # Get all "deepcopy"
        for key, data in locationdata.items():
            location[key] = data

        # Organize and clean
        if location.get("name", None) == location.get("obsname", None):
            location["obsname"] = (
                location.pop("obsname", None)
                + " ("
                + location.pop("obscode", None)
                + ")"
            )
            location.pop("name", None)
            location.pop("code", None)

        return location

    def process_high_low(self, highlowdata=None):
        """Process data for high and low tides."""
        highlow = []
        if highlowdata is None:
            highlowdata = self.highlowdata

        prevtime = None
        for data in highlowdata:
            if data.get("time", None) is not None:
                data["time"] = dt.parse_datetime(data.get("time"))
            if prevtime is not None:
                data["timefromlast"] = str(data["time"] - prevtime)
            prevtime = data["time"]
            highlow.append(data)
        return highlow

    def process_tidedatatime(self, tidedata=None):
        """Process data for detailed tide information."""
        tidedatatime = {}
        if tidedata is None:
            tidedata = self.tidedata

        for data in tidedata.get(API_PREDICTION):
            datadict = {}
            for datatype in tidedata:
                datadict[datatype] = self.findByTime(
                    tidedata.get(datatype), data["time"]
                ).get("value", "NaN")
            tidedatatime[dt.parse_datetime(data["time"])] = datadict
        _LOGGER.debug(f"process_tidedatatime: {len(tidedatatime)}")
        _LOGGER.debug(f"tidedatatime: {tidedatatime}")
        return tidedatatime

    def findByTime(self, datatype, time):
        """Find data by time."""
        for data in datatype:
            if data.get("time") == time:
                return data
        return {}

    def getLocationData(self, compact=True):
        if not compact:
            return self.location
        else:
            return {"place": self.location.get("place", None)}

    def getData(self, tidedatatime=None, type=API_FORECAST):
        """Get list of data [datestamp, data]. Type can be forecast, prediction or observation."""
        if tidedatatime is None:
            tidedatatime = self.tidedatatime

        datalist = []
        for key, data in tidedatatime.items():
            datalist.append([key, data.get(type)])
        _LOGGER.debug(f"getData_list {type}: {datalist}")
        return datalist

    def getDataAll(self, tidedatatime=None):
        """Get list of data [datestamp, data]. """
        if tidedatatime is None:
            tidedatatime = self.tidedatatime

        datalist = []
        for key, data in tidedatatime.items():
            item = {
                "datetime": key,
                "prediction": data.get(API_PREDICTION),
                "forecast": data.get(API_FORECAST),
                "observation": data.get(API_OBSERVATION),
            }
            datalist.append(item)
        _LOGGER.debug(f"getData_list_all: {datalist}")
        return datalist

        # datadict = {}
        # for key, data in tidedatatime.items():
        #     datadict[key.strftime(API_STRINGTIME)] = {
        #         "tidetime": key,
        #         "prediction": data.get(API_PREDICTION),
        #         "forecast": data.get(API_FORECAST),
        #         "observation": data.get(API_OBSERVATION),
        #     }
        # _LOGGER.debug(f"getData_list_all: {datadict}")
        # return datadict

    def getNextTide(self, highlow=None):
        """Get next change in tide."""
        for tide in self.highlow:
            if dt.now() < tide["time"]:
                if highlow is None or tide["flag"] == highlow:
                    _LOGGER.debug(f"getNextTide (highlow={highlow}):  - {tide}")
                    return tide
        return {}

    def getTimeBetweenTideTimes(self, tide1, tide2=None):
        """Get difference between two tide times."""
        if tide2 is None:
            for tide in self.highlow:
                if dt.now() < tide.get("time"):
                    break
                tide2 = dt.parse_datetime(tide.get("time", None))  # previous tide
        return tide1 - tide2

    def getTimeToNextTide(self, nexttide=None, highlow=None):
        """Get time to next change of tide."""
        if nexttide is None and highlow is None:
            nexttide = self.next_tide
        elif highlow is not None:
            nexttide = self.getNextTide(highlow)
        return nexttide.get("time") - dt.now()

    def getTideState(self, nexttide=None):
        """Get state of next change in tide (low/high)."""
        if nexttide is None:
            nexttide = self.getNextTide()

        tidedelta = nexttide.get("time") - dt.now()
        timefromlast = self.parsetimedelta(nexttide.get("timefromlast", 0))
        tidesplit = timefromlast / 6

        _LOGGER.debug(f"getTideState nexttide: {nexttide}")
        _LOGGER.debug(f"getTideState tidedelta: {tidedelta}")

        # Short time to tide change
        if tidedelta <= tidesplit:
            if nexttide.get("flag") == API_LOW:
                return f"{API_LOW}"
            elif nexttide.get("flag") == API_HIGH:
                return f"{API_HIGH}"
        # Long time to tide change, opposite
        elif (timefromlast - tidedelta) <= tidesplit:
            if nexttide.get("flag") == API_LOW:
                return f"{API_HIGH}"
            elif nexttide.get("flag") == API_HIGH:
                return f"{API_LOW}"
        return "Normal"

    def getTideStateEbbFlow(self, nexttide=None):
        """Get direction of tide (ebb/flow)."""
        if nexttide is None:
            nexttide = self.getNextTide()

        if nexttide.get("flag") == API_LOW:
            tidestate = TIDE_EBB  # if next tide is low, then it is ebbing
        elif nexttide.get("flag") == API_HIGH:
            tidestate = TIDE_FLOW  # if next tide is high, then it is flowing
        else:
            tidestate = None
        return tidestate

    def getTideStateFull(self, nexttide=None):
        """Get full tide state including both high/low and ebb/flow."""
        if nexttide is None:
            nexttide = self.getNextTide()
        state = self.getTideState(nexttide)
        if state == "Normal":
            return self.getTideStateEbbFlow(nexttide)
        else:
            return state + " " + self.getTideStateEbbFlow(nexttide)

    def getLastData(self, type=None):
        """Get last data in datatype."""
        data = {}
        for datatype in self.tidedata:
            if type is None or type == datatype:
                data[datatype] = self.tidedata[datatype][-1]
        _LOGGER.debug(f"getLastData (type={type}):  - {data}")
        return data

    def getCurrentData(self, type=None):
        """Get current data i.e. data nearest to actual time."""
        nearest = self.getNearestData(self.tidedatatime, dt.now())
        _LOGGER.debug(f"getCurrentData: {nearest} - {self.tidedatatime[nearest]}")
        return self.tidedatatime[nearest]

    def getCurrentDataObservation(self):
        """Get current observation i.e. observation nearest to actual time."""
        lastobservation = self.getLastData(type=API_OBSERVATION).get(
            API_OBSERVATION, None
        )
        _LOGGER.debug(
            f"Last observation: {lastobservation} with time {lastobservation.get('time')}"
        )
        if lastobservation is not None:
            time = lastobservation.get("time", None)
            return self.tidedatatime.get(dt.parse_datetime(time), None)
        else:
            return None

    def getNearestData(self, items, data):
        """Return the datetime in items which is the closest to the data pivot, datetypes must support comparison and subtraction."""
        return min(items, key=lambda x: abs(x - data))

    def parsetimedelta(self, s):
        """Return a timedelta parsed from string representation."""
        if "day" in s:
            m = re.match(
                r"(?P<days>[-\d]+) day[s]*, (?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>\d[\.\d+]*)",
                s,
            )
        else:
            m = re.match(r"(?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>\d[\.\d+]*)", s)
        return timedelta(**{key: float(val) for key, val in m.groupdict().items()})
