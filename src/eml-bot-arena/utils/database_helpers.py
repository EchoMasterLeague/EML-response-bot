from database.database_full import FullDatabase
from database.enums import Bool
from database.fields import (
    PlayerFields,
    TeamFields,
    TeamPlayerFields,
    VwRosterFields,
)
import constants
import logging

logger = logging.getLogger(__name__)


### Roster ###
async def update_roster_view(
    database: FullDatabase, team_id: str = None, team_name: str = None
):
    """Rebuild Roster for all Teams

    Args:
        db (FullDatabase): The database
        team_id (str, optional): The team_id to update. Defaults to None.
        team_name (str, optional): The team_name to update. Defaults to None.

    Note: team_id and team_name are ignored, this rebuilds the full roster ever time it is called.
    They are kept in case we want to update teams individually in the future.
    """
    all_teams = await database.table_team.get_table_data()
    all_players = await database.table_player.get_table_data()
    all_team_players = await database.table_team_player.get_table_data()
    roster_table = [
        [
            VwRosterFields.team.name,
            VwRosterFields.captain.name,
            VwRosterFields.co_cap_or_2.name,
            VwRosterFields.player_3.name,
            VwRosterFields.player_4.name,
            VwRosterFields.player_5.name,
            VwRosterFields.player_6.name,
            VwRosterFields.active.name,
            VwRosterFields.region.name,
            VwRosterFields.is_2_co_cap.name,
        ]
    ]

    player_name_dict = {}
    for player in all_players:
        if all_players.index(player) == 0:
            continue
        player_id = player[PlayerFields.record_id]
        player_name = player[PlayerFields.player_name]
        player_name_dict[player_id] = player_name

    team_name_dict = {}
    team_region_dict = {}
    for team in all_teams:
        if all_teams.index(team) == 0:
            continue
        team_id = team[TeamFields.record_id]
        team_name = team[TeamFields.team_name]
        team_name_dict[team_id] = team_name
        team_region = team[TeamFields.vw_region]
        team_region_dict[team_id] = team_region

    roster_dict = {}
    for team_player in all_team_players:
        if all_team_players.index(team_player) == 0:
            continue
        # Gather info about this player and team
        team_id = team_player[TeamPlayerFields.team_id]
        player_id = team_player[TeamPlayerFields.player_id]
        is_captain = team_player[TeamPlayerFields.is_captain] == Bool.TRUE
        is_co_captain = team_player[TeamPlayerFields.is_co_captain] == Bool.TRUE
        team_name = team_name_dict.get(team_id)
        player_name = player_name_dict.get(player_id)
        # Update the roster dictionary
        sub_dict_team: dict = roster_dict.get(team_name, {})
        is_any_captain = is_captain or is_co_captain
        if is_captain:
            sub_dict_team["captain"] = player_name
            sub_dict_team["region"] = team_region_dict.get(team_id)
        if is_co_captain:
            sub_dict_team["co_captain"] = player_name
        if not is_any_captain:
            sub_dict_players = sub_dict_team.get("players", []) + [player_name]
            sub_dict_team["players"] = sub_dict_players
        roster_dict[team_name] = sub_dict_team
    # Sort the teams
    roster_dict = dict(sorted(roster_dict.items()))
    # Build the table
    for team_name, sub_dict_team in roster_dict.items():
        region = sub_dict_team.get("region", None)
        captain = sub_dict_team.get("captain", None)
        co_captain = sub_dict_team.get("co_captain", None)
        is_2_co_cap = Bool.TRUE if co_captain else Bool.FALSE
        players: list = sub_dict_team.get("players", [])
        players.sort()
        if co_captain:
            players = [co_captain] + players
        if captain:
            players = [captain] + players
        is_active = len(players) >= constants.TEAM_PLAYERS_MIN
        is_active = Bool.TRUE if is_active else Bool.FALSE
        roster_table.append(
            [
                team_name,
                players[0] if len(players) > 0 else None,
                players[1] if len(players) > 1 else None,
                players[2] if len(players) > 2 else None,
                players[3] if len(players) > 3 else None,
                players[4] if len(players) > 4 else None,
                players[5] if len(players) > 5 else None,
                is_active,
                region,
                is_2_co_cap,
            ]
        )
    await database.table_vw_roster.replace_vw_roster(roster_table)
