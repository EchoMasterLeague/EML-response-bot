from bot_functions import helpers
from database.database import Database
from database import table_team as Team
from database import table_player as Player
from database import table_team_player as TeamPlayer

"""
EML Team Management
"""


async def register_team(
    database: Database, team_name: str, discord_id: str, player_name: str
):
    """Create a Team with the given name

    Process:
    - Check if the Player is registered
    - Check if the Player is already on a Team
    - Check if the Team already exists
    - Create the Team
    - Add the Player as the Captain of the Team
    """
    table_team = Team.Action(database)
    table_player = Player.Action(database)
    table_team_player = TeamPlayer.Action(database)
    # Check if the Player is registered
    player = await table_player.get_player(discord_id=discord_id)
    if not player:
        return f"You must be registered as a player to create a Team."
    # Check if the Player is already on a Team
    team_player = await table_team_player.get_team_player(
        player[Player.Field.record_id.value]
    )
    new_team = await table_team.create_team(team_name)
    if new_team:
        return await helpers.format_json(new_team)
    else:
        old_team = await table_team.get_team(team_name)
        team_name = old_team[Team.Field.team_name.name]
        return f"Team already exists: {team_name}"
    # TODO: continue here


async def get_team_details(database: Database, team_name: str):
    """Get a Team by name"""
    table_team = Team.Action(database)
    response = await table_team.get_team(team_name)
    if not response:
        return f"Team not found: {team_name}"
    return await helpers.format_json(response)
