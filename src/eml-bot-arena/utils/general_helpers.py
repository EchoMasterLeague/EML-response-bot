import json
import datetime
import uuid
import pytz
import constants
import logging

logger = logging.getLogger(__name__)

"""
This module contains common functions for any module.
"""


async def random_id():
    """Generate a random id as a UUID4 string (e.g. 'f47ac10b-58cc-4372-a567-0e02b2c3d479')"""
    random_uuid4_string = str(uuid.uuid4())
    return random_uuid4_string


async def format_json(data, sort_keys=False):
    """Pretty format JSON data"""
    return json.dumps(data, sort_keys=sort_keys, indent=4)


### Time Helpers ###


async def epoch_timestamp(iso_timestamp: str = None) -> int:
    """Return the utc timestamp in epoch format (e.g. 1584661872)"""
    if iso_timestamp is None:
        iso_timestamp = datetime.datetime.now().isoformat()
    epoch_timestamp = datetime.datetime.fromisoformat(iso_timestamp).timestamp()
    return int(epoch_timestamp)


async def iso_timestamp(epoch_timestamp: int = None) -> str:
    """Return the utc timestamp in ISO format (e.g. 2020-03-20T01:31:12.467113+00:00)"""
    if epoch_timestamp is None:
        epoch_timestamp = datetime.datetime.now().timestamp()
    iso_timestamp = datetime.datetime.fromtimestamp(
        epoch_timestamp, tz=datetime.timezone.utc
    ).isoformat()
    return iso_timestamp


async def season_week(epoch_timestamp: int = None) -> str:
    """Return the current season week based on the epoch timestamp (e.g. 202050)"""
    tz = pytz.timezone(constants.TIME_TIMEZONE_EML_OFFICIAL)
    if epoch_timestamp is None:
        epoch_timestamp = datetime.datetime.now().timestamp()
    # Determine year from the timestamp
    year = datetime.datetime.fromtimestamp(epoch_timestamp, tz=tz).year
    # Determine the week of the year from the timestamp
    week = datetime.datetime.fromtimestamp(epoch_timestamp, tz=tz).isocalendar()[1]
    # Calculate the season week
    year_week = f"{year}{week:02d}"
    return year_week


async def upcoming_monday() -> int:
    """Return the epoch timestamp for the following Monday at 00:00:00 UTC

    This will always be the monday within the next 7 days.
    """
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    days_until_monday = (0 - now.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    next_monday = now + datetime.timedelta(days=days_until_monday)
    next_monday_midnight = datetime.datetime.combine(
        next_monday, datetime.time.min.replace(tzinfo=datetime.timezone.utc)
    )
    epoch_time = int(next_monday_midnight.timestamp())
    return epoch_time


### EML Localized Time Helpers ###


async def epoch_from_eml_datetime_strings(
    year: int, month: int, day: int, time: str, am_pm: str
) -> int:
    """Return the epoch time from eml datetime string

    From 'YYYY-MM-DD HH:MMAM/PM'
    To epoch timestamp (e.g. 1584661872)
    """
    try:
        if ":" not in time:
            time = f"{time}:00"
        tz = pytz.timezone(constants.TIME_TIMEZONE_EML_OFFICIAL)
        date_time = f"{year}-{month}-{day} {time}{am_pm}"
        date_time_obj = tz.localize(
            datetime.datetime.strptime(date_time, "%Y-%m-%d %I:%M%p")
        )
        epoch_timestamp = int(date_time_obj.timestamp())
        return epoch_timestamp
    except Exception as e:
        logger.exception(e)
        return None


async def eml_date(epoch_timestamp: int) -> str:
    """Return the date in Eastern Time from the epoch timestamp (e.g. 03/19/2020)"""
    tz = pytz.timezone(constants.TIME_TIMEZONE_EML_OFFICIAL)
    eml_datetime = datetime.datetime.fromtimestamp(epoch_timestamp, tz)
    eml_date = eml_datetime.strftime("%m/%d/%Y")
    return eml_date


async def eml_time(epoch_timestamp: int) -> str:
    """Return the time in Eastern Time from the epoch timestamp (e.g. 1:31 PM)"""
    tz = pytz.timezone(constants.TIME_TIMEZONE_EML_OFFICIAL)
    eml_datetime = datetime.datetime.fromtimestamp(epoch_timestamp, tz)
    eml_time = eml_datetime.strftime("%I:%M %p")
    if eml_time.startswith("0"):
        eml_time = eml_time[1:]
    return eml_time
