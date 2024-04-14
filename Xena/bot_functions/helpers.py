import json
import discord
from database import table_player as Player

"""
This module contains common functions for modules within bot_functions.
"""


async def format_json(data, sort_keys=False):
    """Pretty print JSON data"""
    return json.dumps(data, sort_keys=sort_keys, indent=4)


class DiscordHelpers:
    """Discord Helper Functions"""

    @staticmethod
    async def guild_role_get_or_create(
        guild: discord.Guild, role_name: str
    ) -> discord.Role:
        """Ensure a role exists in the Discord server"""
        existing_role = discord.utils.get(guild.roles, name=role_name)
        if existing_role:
            return existing_role
        return await guild.create_role(name=role_name)

    @staticmethod
    async def guild_role_remove_if_exists(guild: discord.Guild, role_name: str) -> bool:
        """Remove a role from the Discord server if it exists"""
        existing_role = discord.utils.get(guild.roles, name=role_name)
        if existing_role:
            await existing_role.delete()
        return True

    @staticmethod
    async def member_role_add_if_needed(member: discord.Member, role_name: str) -> bool:
        """Add a role to a member if it does not already exist"""
        role = discord.utils.get(member.roles, name=role_name)
        if not role:
            role = await DiscordHelpers.guild_role_get_or_create(
                member.guild, role_name
            )
        await member.add_roles(role)
        return True

    @staticmethod
    async def member_role_remove_by_prefix(
        member: discord.Member, role_prefix: str
    ) -> bool:
        """Remove all roles from a member that match a prefix"""
        for role in member.roles:
            if role.name.startswith(role_prefix):
                await member.remove_roles(role)
        return True


class DatabaseHelpers:
    """Database Helper Functions"""

    @staticmethod
    async def player_record_from_discord_id(
        discord_id: str, table_player: Player.Action
    ) -> bool:
        """Get DB Player record by Discord ID"""
        player = await table_player.get_player(discord_id=discord_id)
        return player
