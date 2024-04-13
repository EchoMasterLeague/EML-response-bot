from bot_functions import helpers
from database.database import Database
from database import table_player as Player


class ManagePlayers:
    """EML Player Management"""

    def __init__(self, database: Database):
        self.database = database
        self.table_player = Player.Action(database)

    async def register_player(self, discord_id: str, player_name: str, region: str):
        """Create a new Player"""
        region = region.upper()
        if region not in [r.value for r in Player.Region]:
            return f"Invalid region: '{region}' provided. Valid regions: {', '.join([r.value for r in Player.Region])}"
        new_player = await self.table_player.create_player(discord_id, player_name)
        if new_player:
            return await helpers.format_json(new_player.to_dict())
        else:
            return f"Player already registered: {player_name} ({discord_id})"

    async def get_player_details(self, player_name: str = None, discord_id: str = None):
        """Get a Player by name or Discord ID"""
        if not player_name and not discord_id:
            return "No player_name or discord_id provided."
        existing_player = await self.table_player.get_player(
            discord_id=discord_id, player_name=player_name
        )
        if existing_player:
            return await helpers.format_json(existing_player.to_dict())
        else:
            return f"Player not found."
