"""Sample API Client."""
import asyncio
import logging
import re
import socket
import xml.etree.ElementTree as ET
import argparse
from datetime import timedelta
from decimal import Decimal
from typing import Optional

import pytz
import aiohttp
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import datetime as dt
import os, sys

DEFAULT_TIME_ZONE: dt.tzinfo = pytz.timezone("Europe/Oslo")
TIMEOUT = 30  # seconds
API_ATTRIBUTION = "Data from ©Kartverket (www.kartverket.no)"
API_ATTRIBUTION_URL = "http://sehavniva.no/"
API_NAME = "norwegiantide"
VERSION = "0.1.2"
API_USER_AGENT = f"{API_NAME}/{VERSION} https://github.com/tmjo/ha-norwegiantide"
API_PREDICTION = "prediction"
API_OBSERVATION = "observation"
API_FORECAST = "forecast"
API_STRINGTIME = "%Y-%m-%dT%H:%M:%S%z"
API_EBB = "ebb"
API_FLOW = "flow"
API_LANG = "nb"
API_LOW = "low"
API_HIGH = "high"
API_LAT = "latitude"
API_LON = "longitude"
API_PLACE = "place"
CONST_DIR_THIS = os.path.split(__file__)[0]
CONST_DIR_DEFAULT = os.path.join(CONST_DIR_THIS, "tmp")

_LOGGER: logging.Logger = logging.getLogger(__package__)

HEADERS = {"Content-type": "application/json; charset=UTF-8"}


class NorwegianTideApiClient:
    def __init__(
        self,
        place,
        latitude,
        longitude,
        session: aiohttp.ClientSession,
        output_dir=CONST_DIR_DEFAULT,
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
        self.output_dir = output_dir
        self.file_image = API_NAME + "_" + self.place + "_img.png"

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
            fromtime = dt_now() - timedelta(hours=12)

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
        try:
            self.location = self.process_location()
            self.tidedatatime = self.process_tidedatatime()
            self.highlow = self.process_high_low()
        # except AttributeError as e:
        except:
            _LOGGER.error(
                f"Unable to read API response - service may be down (try {API_ATTRIBUTION_URL})."
            )
        return self.process_data()

    async def get_xml_data(self):
        try:
            # Get prediction, observation and forecast
            headers = {"User-Agent": API_USER_AGENT}
            response = await self.api_wrapper(
                "get", self.get_url(datatype="all"), headers=headers
            )
            content = await response.text()
            self.locationdata = self.xml_location(content)
            self.tidedata = self.xml_tidedata(content)

            # Get low/high tides table
            response = await self.api_wrapper("get", self.get_url(datatype="tab"))
            content = await response.text()
            self.highlowdata = self.xml_high_low(content)
        # except AttributeError as e:
        except Exception as e:
            _LOGGER.debug(
                f"Unable to decode xml possibly due to previous error getting data. {e}"
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
        self.data = self.getDataAll()

        try:
            self.plot_tidedata()
        except Exception as e:  # pylint: disable=broad-except
            _LOGGER.warning(f"Error processing tide plot: {e}")

        return {
            API_PLACE: self.getLocationPlace(),
            API_LAT: self.getLocation(API_LAT),
            API_LON: self.getLocation(API_LON),
            "location_details": self.getLocationDetails(),
            "next_tide": self.next_tide,
            "next_tide_time": {
                None if self.next_tide is None else self.next_tide.get("time", None)
            },
            "next_tide_low": self.next_tide_low,
            "next_tide_high": self.next_tide_high,
            "time_to_next_tide": self.time_to_next_tide,
            "time_to_next_low": self.time_to_next_low,
            "time_to_next_high": self.time_to_next_high,
            "ebb_flow": self.ebb_flow,
            "ebbing": self.ebb_flow == API_EBB,
            "flowing": self.ebb_flow == API_FLOW,
            "tide_state": self.tide_state_full,
            "highlow": self.highlow,
            "tidedatatime": self.tidedatatime,
            "tidedata": self.tidedata,
            "lastdata": self.last_data,
            "currentdata": self.current_data,
            "currentobservation": self.current_observation,
            "data": self.data,
        }

    async def api_wrapper(
        self, method: str, url: str, data: dict = {}, headers: dict = {}
    ):
        """Get information from the API."""
        try:
            if method == "get":
                response = await self._session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=TIMEOUT)
                )
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
        _LOGGER.debug(f"xml_tidedata: {len(tidedata)} datatypes")
        for k in tidedata.keys():
            _LOGGER.debug(
                f"xml_tidedata - datatype: {k} {len(tidedata.get(k))} entries"
            )
        return tidedata

    def process_location(self, locationdata=None):
        """Process data for location."""
        location = {}
        if locationdata is None:
            locationdata = self.locationdata

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
                data["time"] = dt_parse_datetime(data.get("time"))
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
            tidedatatime[dt_parse_datetime(data["time"])] = datadict
        _LOGGER.debug(f"process_tidedatatime: {len(tidedatatime)}")
        # _LOGGER.debug(f"tidedatatime: {tidedatatime}")
        return tidedatatime

    def findByTime(self, datatype, time):
        """Find data by time."""
        for data in datatype:
            if data.get("time") == time:
                return data
        return {}

    def getLocationPlace(self):
        return {API_PLACE: self.location.get(API_PLACE, None)}

    def getLocation(self, latlon):
        if latlon == API_LAT:
            return self.location.get(API_LAT, None)
        elif latlon == API_LON:
            return self.location.get(API_LON, None)

    def getLocationDetails(self):
        details = {}
        for k, v in self.location.items():
            if k not in [API_PLACE, API_LON, API_LAT]:
                details[k] = v
        return details

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
        """Get list of data [datestamp, data]."""
        if tidedatatime is None:
            tidedatatime = self.tidedatatime

        datalist = []
        for key, data in tidedatatime.items():
            item = {
                "datetime": key,
                API_PREDICTION: data.get(API_PREDICTION),
                API_FORECAST: data.get(API_FORECAST),
                API_OBSERVATION: data.get(API_OBSERVATION),
            }
            datalist.append(item)
        _LOGGER.debug(f"getData_list_all: {len(datalist)}")
        return datalist

    def getNextTide(self, highlow=None):
        """Get next change in tide."""
        try:
            for tide in self.highlow:
                if dt_now() < tide["time"]:
                    if highlow is None or tide["flag"] == highlow:
                        _LOGGER.debug(f"getNextTide (highlow={highlow}):  - {tide}")
                        return tide
        except TypeError:
            return {}

    def getTimeBetweenTideTimes(self, tide1, tide2=None):
        """Get difference between two tide times."""
        if tide2 is None:
            for tide in self.highlow:
                if dt_now() < tide.get("time"):
                    break
                tide2 = dt_parse_datetime(tide.get("time", None))  # previous tide
        return tide1 - tide2

    def getTimeToNextTide(self, nexttide=None, highlow=None):
        """Get time to next change of tide."""
        try:
            if nexttide is None and highlow is None:
                nexttide = self.next_tide
            elif highlow is not None:
                nexttide = self.getNextTide(highlow)

            if nexttide is not None:
                return nexttide.get("time") - dt_now()
            else:
                return None
        # except TypeError:
        except:
            return None

    def getTideState(self, nexttide=None):
        """Get state of next change in tide (low/high)."""
        try:
            if nexttide is None:
                nexttide = self.getNextTide()

            tidedelta = nexttide.get("time") - dt_now()
            timefromlast = parsetimedelta(nexttide.get("timefromlast", 0))
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
        # except TypeError:
        except:
            return None

    def getTideStateEbbFlow(self, nexttide=None):
        """Get direction of tide (ebb/flow)."""
        if nexttide is None:
            nexttide = self.getNextTide()

        if nexttide is None:
            tidestate = None
        elif nexttide.get("flag") == API_LOW:
            tidestate = API_EBB  # if next tide is low, then it is ebbing
        elif nexttide.get("flag") == API_HIGH:
            tidestate = API_FLOW  # if next tide is high, then it is flowing
        else:
            tidestate = None
        return tidestate

    def getTideStateFull(self, nexttide=None):
        """Get full tide state including both high/low and ebb/flow."""
        try:
            if nexttide is None:
                nexttide = self.getNextTide()
            state = self.getTideState(nexttide)
            if state == "Normal":
                return self.getTideStateEbbFlow(nexttide)
            else:
                return state + " " + self.getTideStateEbbFlow(nexttide)
        except TypeError:
            return None

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
        try:
            nearest = self.getNearestData(self.tidedatatime, dt_now())
            _LOGGER.debug(f"getCurrentData: {nearest} - {self.tidedatatime[nearest]}")
            return self.tidedatatime[nearest]
        except:
            return None

    def getCurrentDataObservation(self):
        """Get current observation i.e. observation nearest to actual time."""
        lastobservation = self.getLastData(type=API_OBSERVATION).get(
            API_OBSERVATION, None
        )
        if lastobservation is not None:
            _LOGGER.debug(
                f"Last observation: {lastobservation} with time {lastobservation.get('time')}"
            )
            time = lastobservation.get("time", None)
            return self.tidedatatime.get(dt_parse_datetime(time), None)
        else:
            return None

    def getNearestData(self, items, data):
        """Return the datetime in items which is the closest to the data pivot, datetypes must support comparison and subtraction."""
        try:
            return min(items, key=lambda x: abs(x - data))
        # except TypeError:
        except:
            return None

    def plot_tidedata(
        self, filename=None, show=False, xlength: timedelta = timedelta(hours=36)
    ):

        _LOGGER.debug("Creating plot")
        x = []
        y1 = []
        y2 = []
        y3 = []
        for data in self.data:
            x.append(data.get("datetime"))
            y1.append(float(data.get(API_FORECAST)))
            y2.append(float(data.get(API_PREDICTION)))
            y3.append(float(data.get(API_OBSERVATION)))

        # Min/max/now
        ymin = min(y1 + y2 + y3)
        ymax = max(y1 + y2 + y3)
        now = dt_now()

        # Plot the data
        fig, ax = plt.subplots(1)
        ax.plot(x, y1, label=API_FORECAST, color="green", linewidth=3)
        ax.legend()
        ax.plot(x, y2, label=API_PREDICTION, color="darkorange", linewidth=3)
        ax.legend()
        ax.plot(x, y3, label=API_OBSERVATION, color="blue", linewidth=3)
        ax.legend()

        # Line for 'now' and annotations current value and timestamp
        plt.axvline(x=now, color="red", linestyle="dashed", linewidth=1)
        plt.text(
            now,
            -5,
            f" Forecast {self.current_data.get(API_FORECAST)}cm",
            color="red",
            fontsize=8,
        )
        plt.text(
            now,
            -9,
            f" {now.strftime('%d.%m.%y %H:%M')}",
            color="red",
            fontsize=8,
        )

        # Add high-low timestamps on plot
        self.plot_add_highlow(plt, self.highlow, color="darkorange", fontsize=8)

        # Formatting
        plt.gcf().autofmt_xdate()
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=now.tzinfo))
        ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=120))
        ax.xaxis.set_minor_locator(mdates.MinuteLocator(interval=60))
        ax.tick_params(axis="x", labelsize=8)
        xstart = x[0] - timedelta(hours=1, minutes=x[0].minute)
        ax.set_xlim(xstart, xstart + xlength)
        ax.set(
            title=f"Tide for {self.place} ({self.tide_state_full}ing)",
            ylabel="Waterlevel [cm]",
        )
        plt.xticks(rotation=90, ha="center")
        _LOGGER.debug(f"Plotting from: {xstart} to {xstart+xlength}")

        # Custom scaling
        ylim_min = ymin if ymin < -10 else -10
        ylim_max = ymax if ymax > 140 else 140
        ax.set_ylim([ylim_min, ylim_max])

        # Add a legend
        # plt.legend(bbox_to_anchor=(1, 1), loc="upper left")
        # plt.legend()  # => removed, put on ax instead - avoid No artists with labels found to put in legend. Note that artists whose label start with an underscore are ignored when legend() is called with no argument.

        # Save image
        if filename is None:
            filename = os.path.join(self.output_dir, self.file_image)

        _LOGGER.debug(f"Saving image {filename}.")
        plt.savefig(filename)

        # Show
        if show:
            plt.show()
        plt.close()

    def plot_add_highlow(self, plt, highlow=None, color="darkorange", fontsize=8):
        if highlow is None:
            highlow = self.highlow

        for data in highlow:
            t = data.get("time")
            v = data.get("value")
            f = data.get("flag")
            if f == "high":
                addpos = 5
            else:
                addpos = 20

            plt.text(
                t,
                float(v) + addpos,
                f"{dt_strftime(t, '%H:%M')}\n{v}cm",
                color=color,
                ha="center",
                rotation=90,
                fontsize=fontsize,
            )


def parsetimedelta(s):
    """Return a timedelta parsed from string representation."""
    if "day" in s:
        m = re.match(
            r"(?P<days>[-\d]+) day[s]*, (?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>\d[\.\d+]*)",
            s,
        )
    else:
        m = re.match(r"(?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>\d[\.\d+]*)", s)
    return timedelta(**{key: float(val) for key, val in m.groupdict().items()})


def dt_now(time_zone: Optional[dt.tzinfo] = None) -> dt.datetime:
    """Get now in specified time zone."""
    return dt.datetime.now(time_zone or DEFAULT_TIME_ZONE)


def dt_parse_datetime(dt_str: str) -> Optional[dt.datetime]:
    """Parse string into datetime with API dateformat."""
    try:
        return dt.datetime.strptime(dt_str, API_STRINGTIME)
    except (ValueError, IndexError) as e:
        _LOGGER.debug(f"{dt_str} - PARSE ERROR: {e}")


def dt_strftime(dt_dt: dt.datetime, format=API_STRINGTIME) -> Optional[str]:
    """Parse datetime into string with API dateformat and timezone."""
    try:
        return dt_dt.astimezone(DEFAULT_TIME_ZONE).strftime(format)
    except ValueError as e:
        _LOGGER.debug(f"{dt_dt} - PARSE ERROR: {e}")


def parse_arguments():
    """Argument parser for running API separately."""
    parser = argparse.ArgumentParser(description=f"{API_NAME}: {API_ATTRIBUTION}")
    parser.add_argument(
        "-lat", "--latitude", help="Latitude", required=True, type=float
    )
    parser.add_argument(
        "-lon", "--longitude", help="Longitude", required=True, type=float
    )
    parser.add_argument("-p", "--place", help="Place name", required=False, type=str)
    parser.add_argument(
        "-s", "--show", help="Show plot", required=False, action="store_true"
    )
    args = parser.parse_args()
    return args


async def main():
    """Main function when runing API separately."""
    args = parse_arguments()
    _LOGGER.debug("args: %s", args)
    session = aiohttp.ClientSession()
    tide = NorwegianTideApiClient(
        latitude=args.latitude,
        longitude=args.longitude,
        place=args.place if args.place is not None else "MyLocation",
        session=session,
    )
    tidedata = await tide.async_get_data()

    print("\n\n\n******************************************")
    print(f"Tide for {tidedata.get(tide.place, None)}")
    print(f"Lat: {tidedata.get(API_LON, None)} Lon: {tidedata.get(API_LAT, None)}")
    print(tidedata.get("location_details", None))
    print("******************************************\n\n\n")
    await session.close()
    tide.plot_tidedata(show=args.show)


if __name__ == "__main__":
    import sys

    _LOGGER: logging.Logger = logging.getLogger(__file__)
    _LOGGER.setLevel(logging.DEBUG)
    fh = logging.StreamHandler()
    fh_formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(lineno)d:%(filename)s(%(process)d) - %(message)s"
    )
    fh.setFormatter(fh_formatter)
    _LOGGER.addHandler(fh)
    asyncio.run(main())
