from database.database import Database
from database import table_player as Player
import utils.general_helpers as helpers
import discord
from errors import discord_errors, database_errors


class ManagePlayers:
    """EML Player Management"""

    def __init__(self, database: Database):
        self.database = database
        self.table_player = Player.PlayerTable(database)

    async def respond(self, interaction: discord.Interaction, message: str):
        """Respond to an Interaction"""
        await interaction.response.send_message(message)

    async def register_player(
        self,
        interaction: discord.Interaction,
        region: str,
    ):
        """Create a new Player"""
        discord_id = interaction.user.id
        player_name = interaction.user.name
        region = region
        try:
            new_player = await self.table_player.create_player_record(
                discord_id=discord_id, player_name=player_name, region=region
            )
            if new_player:
                message = f"Player registered: {player_name} ({discord_id})"
            else:
                message = f"Failed to register Player: {player_name} ({discord_id})"
        except database_errors.EmlPlayerAlreadyExists:
            message = f"Player already registered: {player_name} ({discord_id})"
        except database_errors.EmlPlayerRegionNotFound:
            available_regions = [r.value for r in Player.Regions]
            message = f"Region '{region}' not available. Available Regions: {available_regions}"
        await self.respond(interaction, message)

    async def unregister_player(self, interaction: discord.Interaction):
        """Unregister a Player"""
        discord_id = interaction.user.id
        try:
            existing_player = await self.table_player.get_player_record(
                discord_id=discord_id
            )
            await self.table_player.delete_player_record(existing_player)
            message = f"Player unregistered: {player_name} ({discord_id})"
        except database_errors.EmlPlayerNotFound:
            message = f"Player not found: {player_name} ({discord_id})"
        await self.respond(interaction, message)

    async def get_player_details(
        self,
        interaction: discord.Interaction,
        player_name: str = None,
        discord_id: str = None,
    ):
        """Get a Player by name or Discord ID"""
        if not player_name and not discord_id:
            await self.respond(interaction, "No player_name or discord_id provided.")
            return
        try:
            existing_player = await self.table_player.get_player_record(
                discord_id=discord_id, player_name=player_name
            )
        except database_errors.EmlPlayerNotFound:
            existing_player = None
        if existing_player:
            message = await helpers.format_json(existing_player.to_dict())
        else:
            query = f" player_name={player_name}" if player_name else ""
            query += f" discord_id={discord_id}" if discord_id else ""
            message = f"Player not found: {query}"
        await self.respond(interaction, message)
