import utils.general_helpers as bot_helpers
import utils.discord_helpers as DiscordHelpers
from database.related_records import RelatedRecords
from database import table_player as Player
from database import table_team as Team
from database import table_team_player as TeamPlayer
from database.database import Database
import constants
import discord
import errors.database_errors as DbErrors


class ManageTeams:
    """EML Team Management"""

    def __init__(self, database: Database):
        self.database = database
        self.related_records = RelatedRecords(database)
        self.table_team = Team.TeamTable(database)
        self.table_player = Player.PlayerTable(database)
        self.table_team_player = TeamPlayer.TeamPlayerTable(database)

    async def register_team(self, interaction: discord.Interaction, team_name: str):
        """Create a Team with the given name

        Process:
        - Check if the Player is registered
        - Check if the Player is already on a Team
        - Check if the Team already exists
        - Create the Team and Captain Database Records
        - Update Discord roles
        """
        # Check if the Player is registered
        discord_id = interaction.user.id
        player = await self.table_player.get_player_record(discord_id=discord_id)
        if not player:
            return f"You must be registered as a player to create a Team."
        # Check if the Player is already on a Team
        try:
            existing_team = await self.related_records.get_team_from_player(player)
        except DbErrors.EmlTeamPlayerNotFound:
            existing_team = None
        if existing_team:
            return f"You are already on a Team: {await existing_team.get_field(Team.TeamFields.TEAM_NAME.name)}"
        # Check if the Team already exists
        try:
            existing_team = await self.table_team.get_team(team_name=team_name)
        except DbErrors.EmlTeamNotFound:
            existing_team = None
        if existing_team:
            return f"Team already exists: {team_name}"
        # Create the Team and Captain Records
        new_team = await self.related_records.create_new_team_with_captain(
            team_name, player=player
        )
        if not new_team:
            return f"Error: Failed to create Team or add Player as captain: {team_name}"
        # Update Discord roles
        await ManageTeamsHelpers.member_remove_team_roles(interaction.user)
        await ManageTeamsHelpers.member_add_team_role(interaction.user, team_name)
        await ManageTeamsHelpers.member_add_captain_role(
            interaction.user, await player.get_field(Player.PlayerFields.REGION.name)
        )
        # Success
        return f"You are now the captain of Team: {team_name}\n{await self.get_team_details(team_name)}"

    async def add_player_to_team(
        self, interaction: discord.Interaction, player_name: str
    ):
        """Add a Player to a Team by name"""
        captain = await self.table_player.get_player_record(
            discord_id=interaction.user.id
        )
        if not captain:
            return f"You must be registered as a player to add a Player to a Team."
        team_player = await self.table_team_player.get_team_player_records(
            player_id=await captain.get_field(Player.PlayerFields.RECORD_ID.name)
        )
        if not team_player or not self.related_records.is_any_captain(team_player[0]):
            return f"You must be a Team captain to add a Player."
        team: Team.TeamRecord = await self.table_team.get_team(
            team_id=await team_player[0].get_field(
                TeamPlayer.TeamPlayerFields.TEAM_ID.name
            )
        )
        if not team:
            return f"Your Team could not be found."
        player = await self.table_player.get_player_record(player_name=player_name)
        if not player:
            return f"Player not found: {player_name}"
        existing_team = await self.related_records.get_team_from_player(player)
        if existing_team:
            return f"Player is already on a Team: {await existing_team.get_field(Team.TeamFields.TEAM_NAME.name)}"
        await self.table_team_player.create_team_player_record(
            team_id=await team.get_field(Team.TeamFields.RECORD_ID.name),
            player_id=await player.get_field(Player.PlayerFields.RECORD_ID.name),
        )
        # Update Discord roles
        discord_member = await ManageTeamsHelpers.member_from_discord_id(
            guild=interaction.guild,
            discord_id=await player.get_field(Player.PlayerFields.DISCORD_ID.name),
        )
        team_name = await team.get_field(Team.TeamFields.TEAM_NAME.name)
        await ManageTeamsHelpers.member_remove_team_roles(discord_member)
        await ManageTeamsHelpers.member_add_team_role(discord_member, team_name)
        return f"Player '{player_name}' added to Team '{team_name}'"

    async def get_team_details(self, team_name: str):
        """Get a Team by name"""
        try:
            team = await self.table_team.get_team(team_name=team_name)
        except DbErrors.EmlTeamNotFound:
            team = None
        if not team:
            return f"Team not found: {team_name}"
        players = await self.related_records.get_player_records_from_team(team)
        response = {
            "team": team.to_dict(),
            "players": [player.to_dict() for player in players],
        }
        return await bot_helpers.format_json(response)


class ManageTeamsHelpers:
    """EML Team Management Helpers"""

    ### DISCORD ###

    @staticmethod
    async def member_from_discord_id(guild: discord.Guild, discord_id: str):
        """Get a Guild Member from a Discord ID"""
        member = guild.get_member(discord_id)
        member = await guild.fetch_member(discord_id) if not member else member

        return member

    @staticmethod
    async def member_remove_team_roles(member: discord.Member):
        """Remove all Team roles from a Guild Member"""
        prefixes = [constants.ROLE_PREFIX_TEAM, constants.ROLE_PREFIX_CAPTAIN]
        for role in member.roles:
            if any(role.name.startswith(prefix) for prefix in prefixes):
                await member.remove_roles(role)
        return True

    @staticmethod
    async def member_add_team_role(member: discord.Member, team_name: str):
        """Add a Team role to a Guild Member"""
        role_name = f"{constants.ROLE_PREFIX_TEAM}{team_name}"
        role = await DiscordHelpers.guild_role_get_or_create(member.guild, role_name)
        await member.add_roles(role)
        return True

    @staticmethod
    async def member_add_captain_role(member: discord.Member, region: str):
        """Add a Captain role to a Guild Member"""
        role_name = f"{constants.ROLE_PREFIX_CAPTAIN}{region}"
        role = await DiscordHelpers.guild_role_get_or_create(member.guild, role_name)
        await member.add_roles(role)
        return True

    ### DATABASE ###
