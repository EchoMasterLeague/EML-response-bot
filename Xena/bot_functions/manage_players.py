from database.database import Database
from utils import discord_helpers, general_helpers
import discord
from errors import discord_errors, database_errors
from database.table_player import PlayerFields, PlayerRecord, PlayerTable, Regions
from database.table_team import TeamFields, TeamRecord, TeamTable
from database.table_team_player import (
    TeamPlayerFields,
    TeamPlayerRecord,
    TeamPlayerTable,
)
from database.related_records import RelatedRecords


class ManagePlayers:
    """EML Player Management"""

    def __init__(self, database: Database):
        self.database = database
        self.table_player = PlayerTable(database)
        self.table_team = TeamTable(database)
        self.table_team_player = TeamPlayerTable(database)
        self.related_records = RelatedRecords(database)

    async def register_player(
        self,
        interaction: discord.Interaction,
        region: str,
    ):
        """Create a new Player"""
        try:
            await discord_helpers.response_deferral(interaction)
            discord_id = interaction.user.id
            player_name = interaction.user.display_name
            try:
                new_player = await self.table_player.create_player_record(
                    discord_id=discord_id, player_name=player_name, region=region
                )
                if new_player:
                    message = f"Player registered: {player_name} ({discord_id})"
                else:
                    message = f"Failed to register Player: {player_name} ({discord_id})"
            except database_errors.EmlRecordAlreadyExists:
                message = f"Player already registered: {player_name} ({discord_id})"
            except database_errors.EmlRegionNotFound:
                available_regions = [r.value for r in Regions]
                message = f"Region '{region}' not available. Available Regions: {available_regions}"
            await discord_helpers.response_followup(interaction, message)
        except Exception as error:
            message = f"Error: Something went wrong."
            await discord_helpers.response_followup(interaction, message)
            raise error

    async def unregister_player(self, interaction: discord.Interaction):
        """Unregister a Player"""
        try:
            discord_id = interaction.user.id
            existing_player = await self.table_player.get_player_record(
                discord_id=discord_id
            )
            if not existing_player:
                message = f"You are not registered."
                await discord_helpers.response_followup(interaction, message)
                return
            existing_player_id = await existing_player.get_field(PlayerFields.record_id)
            existing_team_players = (
                await self.table_team_player.get_team_player_records(
                    player_id=existing_player_id
                )
            )
            existing_team_player = (
                existing_team_players[0] if existing_team_players else None
            )
            if existing_team_player:
                message = f"You must leave your team before unregistering."
                await discord_helpers.response_followup(interaction, message)
                return
            await self.table_player.delete_player_record(existing_player)
            message = f"You are no longer registered as a player"
            await discord_helpers.response_followup(interaction, message)
        except Exception as error:
            message = f"Error: Something went wrong."
            await discord_helpers.response_followup(interaction, message)
            raise error

    async def get_player_details(
        self,
        interaction: discord.Interaction,
        player_name: str = None,
        discord_id: str = None,
    ):
        """Get a Player by name or Discord ID"""
        try:
            await discord_helpers.response_deferral(interaction)
            if not player_name and not discord_id:
                message = "No player_name or discord_id provided."
                await discord_helpers.response_followup(interaction, message)
                return
            existing_player = await self.table_player.get_player_record(
                discord_id=discord_id, player_name=player_name
            )
            if not existing_player:
                message = f"Player not found."
                await discord_helpers.response_followup(interaction, message)
                return
            player_dict = await existing_player.to_dict()
            existing_team = await self.related_records.get_team_from_player(
                existing_player
            )
            team_dict = await existing_team.to_dict() if existing_team else None
            message_dict = {
                "player": player_dict,
                "team": team_dict,
            }
            message = await general_helpers.format_json(message_dict)
            await discord_helpers.response_followup(interaction, message)
        except Exception as error:
            message = f"Error: Something went wrong."
            await discord_helpers.response_followup(interaction, message)
            raise error


class ManagePlayersHelpers:
    """EML Player Management Helpers"""

    pass
