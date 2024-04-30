import datetime
import uuid

"""
This module contains helper functions for the database module and associated table-specific modules.
This module is generalized for use in any table module.
"""


async def iso_timestamp(epoch_timestamp: int = None):
    """Return the utc timestamp in ISO format (e.g. 2020-03-20T01:31:12.467113+00:00)"""
    if epoch_timestamp is None:
        epoch_timestamp = datetime.datetime.now().timestamp()
    iso_timestamp = datetime.datetime.fromtimestamp(
        epoch_timestamp, tz=datetime.timezone.utc
    ).isoformat()
    return iso_timestamp


async def epoch_timestamp(iso_timestamp: str = None):
    """Return the utc timestamp in epoch format (e.g. 1584661872)"""
    if iso_timestamp is None:
        iso_timestamp = datetime.datetime.now().isoformat()
    epoch_timestamp = datetime.datetime.fromisoformat(iso_timestamp).timestamp()
    return int(epoch_timestamp)


async def next_monday_epoch():
    """Return the epoch timestamp for the next Monday at 00:00:00 UTC"""
    today = datetime.datetime.now(tz=datetime.timezone.utc).date()
    days_ahead = (0 - today.weekday() + 1) % 7
    next_monday = today + datetime.timedelta(days=days_ahead)
    next_monday_utc = datetime.datetime.combine(next_monday, datetime.time(0, 0))
    epoch_time = int(next_monday_utc.timestamp())
    return epoch_time


async def random_id():
    """Generate a random id as a UUID4 string (e.g. 'f47ac10b-58cc-4372-a567-0e02b2c3d479')"""
    random_uuid4_string = str(uuid.uuid4())
    return random_uuid4_string
