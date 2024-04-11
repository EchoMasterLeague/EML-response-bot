import json

"""
This module contains common functions for modules within bot_functions.
"""


async def format_json(data, sort_keys=False):
    """Pretty print JSON data"""
    return json.dumps(data, sort_keys=sort_keys, indent=4)
