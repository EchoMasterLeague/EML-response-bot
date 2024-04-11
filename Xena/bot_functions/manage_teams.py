from bot_functions import helpers
from database.database import Database
from database import table_team as Team

"""
EML Team Management
"""


async def register_team(database: Database, team_name: str):
    """Create a Team with the given name"""
    team = Team.Action(database)
    new_team = await team.create_team(team_name)
    if new_team:
        return await helpers.format_json(new_team)
    else:
        old_team = await team.get_team(team_name)
        team_name = old_team[Team.Field.team_name.name]
        return f"Team already exists: {team_name}"


async def get_team_details(database: Database, team_name: str):
    """Get a Team by name"""
    team = Team.Action(database)
    response = await team.get_team(team_name)
    if not response:
        return f"Team not found: {team_name}"
    return await helpers.format_json(response)
