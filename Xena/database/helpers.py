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


async def random_id():
    """Generate a random id as a UUID4 string (e.g. 'f47ac10b-58cc-4372-a567-0e02b2c3d479')"""
    random_uuid4_string = str(uuid.uuid4())
    return random_uuid4_string
