from bot_functions import helpers
from database.database import Database
from database import table_player as Player

"""
EML Player Management
"""


async def register_player(database: Database, discord_id: str, player_name: str):
    """Create a new Player"""
    player = Player.Action(database)
    new_player = await player.create_player(discord_id, player_name)
    if new_player:
        return await helpers.format_json(new_player.to_dict())
    else:
        return f"Player already exists: {player_name} ({discord_id})"


async def get_player_details(
    database: Database, player_name: str = None, discord_id: str = None
):
    """Get a Player by name or Discord ID"""
    player = Player.Action(database)
    existing_player = await player.get_player(
        discord_id=discord_id, player_name=player_name
    )
    if existing_player:
        return await helpers.format_json(existing_player.to_dict())
    else:
        return "No player_name or discord_id provided."
