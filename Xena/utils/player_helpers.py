from database.enums import Regions
from utils import discord_helpers
import constants
import discord


async def member_add_player_role(member: discord.Member, region: str):
    """Add a Player role to a Guild Member"""
    role_name = f"{constants.DISCORD_ROLE_PREFIX_PLAYER}{region}"
    role = await discord_helpers.guild_role_get_or_create(member.guild, role_name)
    await member.add_roles(role)
    return True


async def member_remove_player_role(member: discord.Member):
    """Remove a Player role from a Guild Member"""
    prefixes = [constants.DISCORD_ROLE_PREFIX_PLAYER]
    for role in member.roles:
        if any(role.name.startswith(prefix) for prefix in prefixes):
            await member.remove_roles(role)
    return True


async def member_add_league_sub_role(member: discord.Member):
    """Add the League Substitute role to a Guild Member"""
    role = await discord_helpers.guild_role_get_or_create(
        guild=member.guild, role_name=constants.DISCORD_ROLE_LEAGUE_SUB
    )
    await member.add_roles(role)
    return True


async def member_remove_league_sub_role(member: discord.Member):
    """Remove the League Substitute role from a Guild Member"""
    for role in member.roles:
        if role.name == constants.DISCORD_ROLE_LEAGUE_SUB:
            await member.remove_roles(role)
    return True


async def normalize_region(region: str):
    """Normalize a region string"""
    allowed_regions = [r.value for r in Regions]
    for allowed_region in allowed_regions:
        if str(region).casefold() == str(allowed_region).casefold():
            return allowed_region
    return None
