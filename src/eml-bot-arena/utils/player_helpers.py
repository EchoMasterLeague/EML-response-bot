from database.enums import Regions
from utils import discord_helpers
import constants
import discord


async def normalize_region(region: str):
    """Normalize a region string"""
    allowed_regions = [r.value for r in Regions]
    for allowed_region in allowed_regions:
        if str(region).casefold() == str(allowed_region).casefold():
            return allowed_region
    return None
