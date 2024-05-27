import json
import datetime
import uuid
import pytz

"""
This module contains common functions for any module.
"""


async def random_id():
    """Generate a random id as a UUID4 string (e.g. 'f47ac10b-58cc-4372-a567-0e02b2c3d479')"""
    random_uuid4_string = str(uuid.uuid4())
    return random_uuid4_string


async def format_json(data, sort_keys=False):
    """Pretty print JSON data"""
    return json.dumps(data, sort_keys=sort_keys, indent=4)


async def epoch_timestamp(iso_timestamp: str = None) -> int:
    """Return the utc timestamp in epoch format (e.g. 1584661872)"""
    if iso_timestamp is None:
        iso_timestamp = datetime.datetime.now().isoformat()
    epoch_timestamp = datetime.datetime.fromisoformat(iso_timestamp).timestamp()
    return int(epoch_timestamp)


async def epoch_timestamp_from_date_time_zone(
    date: str, time: str, timezone: str
) -> int:
    """Return the utc timestamp in epoch format (e.g. 1584661872)

    This function takes a date, time, and timezone and converts it to an epoch timestamp.

    Args:
        date (str): The date in the format 'YYYY-MM-DD'
        time (str): The time in the format 'HH:MM' with AM/PM
        timezone (str): The timezone in the format 'US/Eastern'
    """
    date_time = f"{date} {time} {timezone}"
    date_time_obj = datetime.datetime.strptime(date_time, "%Y-%m-%d %I:%M %p %Z")
    epoch_timestamp = int(date_time_obj.timestamp())
    return epoch_timestamp


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
    if epoch_timestamp is None:
        epoch_timestamp = datetime.datetime.now().timestamp()
    # Determine year in UTC from the timestamp
    year = datetime.datetime.fromtimestamp(
        epoch_timestamp, tz=datetime.timezone.utc
    ).year
    # Determine the week of the year in UTC from the timestamp
    week = datetime.datetime.fromtimestamp(
        epoch_timestamp, tz=datetime.timezone.utc
    ).isocalendar()[1]
    # Calculate the season week
    year_week = f"{year}{week:02d}"
    return year_week


async def eml_date(epoch_timestamp: int) -> str:
    """Return the date in Eastern Time from the epoch timestamp (e.g. 03/19/2020)"""
    tz = pytz.timezone("America/New_York")
    eastern_time = datetime.datetime.fromtimestamp(epoch_timestamp, tz)
    date_eastern = eastern_time.strftime("%m/%d/%Y")
    return date_eastern


async def eml_time(epoch_timestamp: int) -> str:
    """Return the time in Eastern Time from the epoch timestamp (e.g. 1:31 PM)"""

    # get time in tz
    tz = pytz.timezone("America/New_York")
    eastern_time = datetime.datetime.fromtimestamp(epoch_timestamp, tz)
    time_eastern = eastern_time.strftime("%I:%M %p")
    if time_eastern.startswith("0"):
        time_eastern = time_eastern[1:]
    return time_eastern


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
