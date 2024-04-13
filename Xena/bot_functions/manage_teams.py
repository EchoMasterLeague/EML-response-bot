from bot_functions import helpers
from database.database import Database
from database import table_team as Team
from database import table_player as Player
from database import table_team_player as TeamPlayer
import discord
import constants


class DiscordHelpers:
    """Discord Helper Functions"""

    @staticmethod
    async def guild_create_role(guild: discord.Guild, role_name: str):
        """Create a new role in the Discord server"""
        existing_role = await DiscordHelpers.guild_get_role(guild, role_name)
        if existing_role:
            return None
        return await guild.create_role(name=role_name)

    @staticmethod
    async def guild_get_role(guild: discord.Guild, role_name: str):
        """Get a role from the Discord server"""
        return discord.utils.get(guild.roles, name=role_name)

    @staticmethod
    async def guild_get_all_roles(guild: discord.Guild):
        """Get all roles from the Discord server"""
        return await guild.fetch_roles()

    @staticmethod
    async def guild_remove_role(guild: discord.Guild, role: discord.Role):
        """Remove a role from the Discord server"""
        return await role.delete()

    @staticmethod
    async def user_add_role(member: discord.Member, role: discord.Role):
        """Add a role to a member in the Discord server"""
        existing_role = DiscordHelpers.user_get_role(member, role.name)
        if existing_role:
            return None
        return await member.add_roles(role)

    @staticmethod
    async def user_get_role(member: discord.Member, role_name: str):
        """Get a role from a member in the Discord server"""
        return discord.utils.get(member.roles, name=role_name)

    @staticmethod
    async def user_get_all_roles(member: discord.Member):
        """Get all roles from a member in the Discord server"""
        return member.roles

    @staticmethod
    async def user_remove_role(member: discord.Member, role: discord.Role):
        """Remove a role from a member in the Discord server"""
        return await member.remove_roles(role)

    @staticmethod
    async def user_remove_team_roles(member: discord.Member):
        """Remove all team roles from a member in the Discord server"""
        for role in member.roles:
            if role.name.startswith(constants.ROLE_PREFIX_TEAM):
                await member.remove_roles(role)
        return True


class ManageTeams:
    """EML Team Management"""

    def __init__(self, database: Database):
        self.database = database
        self.table_team = Team.Action(database)
        self.table_player = Player.Action(database)
        self.table_team_player = TeamPlayer.Action(database)

    async def register_team(
        self,
        interaction: discord.Interaction,
        team_name: str,
        discord_id: str,
    ):
        """Create a Team with the given name

        Process:
        - Check if the Player is registered
        - Check if the Player is already on a Team
        - Check if the Team already exists
        - Create the Team
        - Add the Player as the Captain of the Team
        - Create new team role in discord
        - Add team role to player
        - Add captain role to player
        """
        # Check if the Player is registered
        player = await self.table_player.get_player(discord_id=discord_id)
        if not player:
            return f"You must be registered as a player to create a Team."
        # Check if the Player is already on a Team
        team_players = await self.table_team_player.get_team_player_records(
            player_id=player.to_dict()[Player.Field.record_id.name]
        )
        if team_players:
            existing_team = await self.table_team.get_team(
                team_id=team_players[0].to_dict()[TeamPlayer.Field.team_id.name]
            )
            return f"You are already on a Team: {existing_team.to_dict()[Team.Field.team_name.name]}"
        # Check if the Team already exists
        existing_team = await self.table_team.get_team(team_name=team_name)
        if existing_team:
            return f"Team already exists: {team_name}"
        # Create the Team
        new_team = await self.table_team.create_team(team_name)
        # Add the Player as the Captain of the Team
        if not new_team:
            return f"Error: Failed to create Team: {team_name}"
        new_team_player = await self.table_team_player.create_team_player(
            new_team.to_dict()[Team.Field.record_id.name],
            player.to_dict()[Player.Field.record_id.name],
            is_captain=True,
            is_co_captain=False,
        )
        if not new_team_player:
            return f"Error: Failed to add player to Team: {team_name}"
        # Create new team role in discord
        team_role_name = f"{constants.ROLE_PREFIX_TEAM}{team_name}"
        team_role = DiscordHelpers.guild_create_role(interaction.guild, team_role_name)
        if not team_role:
            return f"Error: Failed to create Team role: {team_role_name}"
        # Remove all team roles from player
        await DiscordHelpers.user_remove_team_roles(interaction.message.author)
        # Add team role to player
        new_captain = interaction.message.author
        await new_captain.add_roles(captain_role)
        # Add region-specific captain role to player
        region = player.to_dict()[Player.Field.region.name]
        captain_role_name = f"{constants.ROLE_PREFIX_CAPTAIN}{region}"
        captain_role = await DiscordHelpers.guild_get_role(
            interaction.guild, captain_role_name
        )
        if not captain_role:
            print(f"Creating new role: {captain_role_name}")
            captain_role = await DiscordHelpers.guild_create_role(
                interaction.guild, captain_role_name
            )
        await new_captain.add_roles(captain_role)
        # Success
        return f"You are now the captain of Team: {team_name}"

    async def get_team_details(self, team_name: str):
        """Get a Team by name"""
        response = await self.table_team.get_team(team_name=team_name)
        if not response:
            return f"Team not found: {team_name}"
        return await helpers.format_json(response.to_dict())
