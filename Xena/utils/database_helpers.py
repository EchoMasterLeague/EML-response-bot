import datetime
import uuid
import constants
from database.database_full import FullDatabase
from database.records import (
    PlayerRecord,
    TeamRecord,
    TeamInviteRecord,
    TeamPlayerRecord,
)
from database.enums import Bool, TeamStatus
from database.fields import (
    PlayerFields,
    TeamFields,
    TeamPlayerFields,
    TeamInviteFields,
    VwRosterFields,
)
import utils.general_helpers as general_helpers


### Roster ###
async def update_roster_view(
    db: FullDatabase, team_id: str = None, team_name: str = None
):
    """Rebuild Roster for all Teams

    Args:
        db (FullDatabase): The database
        team_id (str, optional): The team_id to update. Defaults to None.
        team_name (str, optional): The team_name to update. Defaults to None.

    Note: team_id and team_name are ignored, this rebuilds the full roster ever time it is called.
    They are kept in case we want to update teams individually in the future.
    """
    all_teams = await db.table_team.get_table_data()
    all_players = await db.table_player.get_table_data()
    all_team_players = await db.table_team_player.get_table_data()
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
        captain = sub_dict_team.get("captain", None)
        co_captain = sub_dict_team.get("co_captain", None)
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
            ]
        )
    await db.table_vw_roster.write_all_vw_roster_records(roster_table)


### Player ###


async def get_player_details_from_discord_id(
    db: FullDatabase,
    discord_id: str,
    assert_player: bool = True,
):
    """Get Player Details from a Discord ID"""
    player = await db.table_player.get_player_record(discord_id=discord_id)
    if assert_player:
        assert player, f"Player is not registered"
    if not player:
        return None
    return player


### Team ###
class TeamDetailsOfPlayer:
    def __init__(self):
        self.player: PlayerRecord = None
        self.is_captain: bool = False
        self.is_co_captain: bool = False
        self.is_any_captain: bool = False
        self.team: TeamRecord = None
        self.team_players: list[TeamPlayerRecord] = []


class TeamDetails:
    def __init__(self):
        self.team: TeamRecord = None
        self.team_captain: PlayerRecord = None
        self.team_co_captain: PlayerRecord = None
        self.all_players: list[PlayerRecord] = []


async def get_team_details_from_player(
    db: FullDatabase,
    player: PlayerRecord,
    assert_player: bool = True,
    assert_team: bool = True,
    assert_captain: bool = False,
    assert_co_captain: bool = False,
    assert_any_captain: bool = False,
) -> TeamDetailsOfPlayer:
    """Get Team Details from a Discord ID"""
    details = TeamDetailsOfPlayer()
    # Get player from discord_id
    if assert_player:
        assert player, f"Player is not registered, cannot get their team details."
    if not player:
        return details
    details.player = player
    player_name = await player.get_field(PlayerFields.player_name)
    # Get team_player from player
    player_id = await player.get_field(PlayerFields.record_id)
    team_players = await db.table_team_player.get_team_player_records(
        player_id=player_id
    )
    if assert_team:
        assert team_players, f"Player `{player_name}` is not on a team."
    if not team_players:
        return details
    team_player = team_players[0]
    is_captain = await team_player.get_field(TeamPlayerFields.is_captain)
    is_co_captain = await team_player.get_field(TeamPlayerFields.is_co_captain)
    is_any_captain = is_captain or is_co_captain
    details.is_captain = is_captain
    details.is_co_captain = is_co_captain
    details.is_any_captain = is_any_captain
    if assert_captain:
        assert is_captain, f"Player `{player_name}` is not the main captain."
    if assert_co_captain:
        assert is_co_captain, f"Player `{player_name}` is not the co-captain."
    if assert_any_captain:
        assert is_any_captain, f"Player `{player_name}` is not any captain."
    # Get team from team_player
    team_id = await team_player.get_field(TeamPlayerFields.team_id)
    team = await db.table_team.get_team_record(record_id=team_id)
    if assert_team:
        assert team, f"Team no longer exists."
    if not team:
        return details
    details.team = team
    # Get team_players from team
    team_players = await db.table_team_player.get_team_player_records(team_id=team_id)
    details.team_players = team_players
    # Success
    return details


async def get_team_details_from_team(
    db: FullDatabase,
    team: TeamRecord,
    assert_team: bool = True,
    assert_players: bool = True,
    assert_captain: bool = True,
    assert_co_captain: bool = False,
) -> TeamDetails:
    """Get Team Details from a Team Name"""
    details = TeamDetails()
    # Get team from team_name
    if assert_team:
        assert team, f"Team not found."
    if not team:
        return details
    details.team = team
    team_name = await team.get_field(TeamFields.team_name)
    # Get team_players from team
    team_id = await team.get_field(TeamFields.record_id)
    team_players = await db.table_team_player.get_team_player_records(team_id=team_id)
    if assert_players:
        assert team_players, f"Team `{team_name}` has no players."
    if not team_players:
        return details
    # Get players and captains from team_players
    for team_player in team_players:
        is_captain = await team_player.get_field(TeamPlayerFields.is_captain)
        is_co_captain = await team_player.get_field(TeamPlayerFields.is_co_captain)
        player_id = await team_player.get_field(TeamPlayerFields.player_id)
        player = await db.table_player.get_player_record(record_id=player_id)
        if is_captain:
            details.team_captain = player
        if is_co_captain:
            details.team_co_captain = player
        details.all_players.append(player)
    # Assert captains
    if assert_captain:
        assert details.team_captain, f"Team `{team_name}` has no captain."
    if assert_co_captain:
        assert details.team_co_captain, f"Team `{team_name}` has no co-captain."
    # Success
    return details


async def create_team(
    db: FullDatabase,
    player_id: str,
    team_name: str,
):
    """Create a Team"""
    player = await db.table_player.get_player_record(record_id=player_id)
    assert player, f"Player not found."
    player_name = await player.get_field(PlayerFields.player_name)
    # Check if team already exists
    team = await db.table_team.get_team_record(team_name=team_name)
    assert not team, f"Team `{team_name}` already exists."
    # Check if captain is already on a team
    player_team_players = await db.table_team_player.get_team_player_records(
        player_id=player_id
    )
    assert not player_team_players, f"Player is already on a team."
    # Create the team
    player_region = await player.get_field(PlayerFields.region)
    new_team = await db.table_team.create_team_record(
        team_name=team_name, vw_region=player_region
    )

    assert new_team, f"Error: Could not create Team."
    # Add the captain to the team
    team_id = await new_team.get_field(TeamFields.record_id)
    new_team_player = await db.table_team_player.create_team_player_record(
        team_id=team_id,
        player_id=player_id,
        is_captain=True,
        team_name=team_name,
        player_name=player_name,
    )
    assert new_team_player, f"Error: Could not add Captain to Team."
    return new_team


async def add_player_to_team(
    db: FullDatabase,
    player_id: str,
    team_name: str,
):
    """Add a Player to a Team"""
    # Get info about team
    team = await db.table_team.get_team_record(team_name=team_name)
    assert team, f"Team `{team_name}` not found."
    team_name = await team.get_field(TeamFields.team_name)
    team_id = await team.get_field(TeamFields.record_id)
    team_players = await db.table_team_player.get_team_player_records(team_id=team_id)
    assert team_players, f"Team `{team_name}` no longer exists."
    player_count = len(team_players)
    player_limit = constants.TEAM_PLAYERS_MAX
    assert player_count < player_limit, f"Team `{team_name}` is full."
    # Get info about player
    player = await db.table_player.get_player_record(record_id=player_id)
    assert player, f"Player not found."
    player_name = await player.get_field(PlayerFields.player_name)
    player_team_players = await db.table_team_player.get_team_player_records(
        player_id=player_id
    )
    assert not player_team_players, f"Player is already on a team."
    # Add the player to the team
    new_team_player = await db.table_team_player.create_team_player_record(
        team_id=team_id,
        player_id=player_id,
        team_name=team_name,
        player_name=player_name,
    )
    assert new_team_player, f"Error: Could not add Player to Team."
    # Update team status
    is_active = await team.get_field(TeamFields.status) == TeamStatus.ACTIVE
    if not is_active and player_count + 1 >= constants.TEAM_PLAYERS_MIN:
        await team.set_field(TeamFields.status, TeamStatus.ACTIVE)
        await db.table_team.update_team_record(team)
    # Success
    return new_team_player


async def remove_player_from_team(db: FullDatabase, player_id: str, team_id: str):
    """Remove a Player from a Team"""
    # Get info about team
    team_players = await db.table_team_player.get_team_player_records(team_id=team_id)
    captain_id = None
    co_captain_id = None
    this_team_player = None
    for team_player in team_players:
        if await team_player.get_field(TeamPlayerFields.is_captain):
            captain_id = await team_player.get_field(TeamPlayerFields.player_id)
        if await team_player.get_field(TeamPlayerFields.is_co_captain):
            co_captain_id = await team_player.get_field(TeamPlayerFields.player_id)
        if await team_player.get_field(TeamPlayerFields.player_id) == player_id:
            this_team_player = team_player
    assert this_team_player, f"Player is not on the team."
    player_count = len(team_players)
    assert (
        co_captain_id or player_id != captain_id or player_count == 1
    ), f"Team cannot be without a captain, promote another player first."
    # Apply cooldown
    player_name = await this_team_player.get_field(TeamPlayerFields.vw_player)
    team_name = await this_team_player.get_field(TeamPlayerFields.vw_team)
    new_cooldown = await db.table_cooldown.create_cooldown_record(
        player_id=player_id,
        old_team_id=team_id,
        player_name=player_name,
        old_team_name=team_name,
    )
    assert new_cooldown, f"Error: Could not apply cooldown."
    # Remove the player from the team
    await db.table_team_player.delete_team_player_record(this_team_player)
    # Update team status
    team = await db.table_team.get_team_record(record_id=team_id)
    assert team, f"Team not found."
    is_active = await team.get_field(TeamFields.status) == TeamStatus.ACTIVE
    if is_active and player_count - 1 < constants.TEAM_PLAYERS_MIN:
        await team.set_field(TeamFields.status, TeamStatus.INACTIVE)
        await db.table_team.update_team_record(team)
    # Success
    return True


async def promote_player_to_co_captain(
    db: FullDatabase, player: PlayerRecord, team_id: str
):
    """Promote a Player to Co-Captain of a Team"""
    # Get info about player
    player_name = await player.get_field(PlayerFields.player_name)
    player_id = await player.get_field(PlayerFields.record_id)
    # Get info about team
    team_players = await db.table_team_player.get_team_player_records(team_id=team_id)
    captain_id = None
    co_captain_id = None
    this_team_player = None
    for team_player in team_players:
        if await team_player.get_field(TeamPlayerFields.is_captain):
            captain_id = await team_player.get_field(TeamPlayerFields.player_id)
        if await team_player.get_field(TeamPlayerFields.is_co_captain):
            co_captain_id = await team_player.get_field(TeamPlayerFields.player_id)
        if await team_player.get_field(TeamPlayerFields.player_id) == player_id:
            this_team_player = team_player
    assert this_team_player, f"Player `{player_name}` is not on the team."
    assert player_id != captain_id, f"Player `{player_name}` is already the captain."
    assert player_id != co_captain_id, f"Player `{player_name}` is already Co-Captain."
    assert not co_captain_id, f"Team already has a Co-Captain."
    # Promote the player
    await this_team_player.set_field(TeamPlayerFields.is_co_captain, True)
    await db.table_team_player.update_team_player_record(this_team_player)
    # Success
    return True


async def demote_player_from_co_captain(
    db: FullDatabase, player: PlayerRecord, team_id: str
):
    """Demote a Player from Co-Captain of a Team"""
    # Get info about player
    player_name = await player.get_field(PlayerFields.player_name)
    player_id = await player.get_field(PlayerFields.record_id)
    # Get info about team
    team_players = await db.table_team_player.get_team_player_records(team_id=team_id)
    captain_id = None
    co_captain_id = None
    this_team_player = None
    for team_player in team_players:
        if await team_player.get_field(TeamPlayerFields.is_captain):
            captain_id = await team_player.get_field(TeamPlayerFields.player_id)
        if await team_player.get_field(TeamPlayerFields.is_co_captain):
            co_captain_id = await team_player.get_field(TeamPlayerFields.player_id)
        if await team_player.get_field(TeamPlayerFields.player_id) == player_id:
            this_team_player = team_player
    assert this_team_player, f"Player `{player_name}` is not on the team."
    assert player_id != captain_id, f"Player `{player_name}` is the captain."
    assert player_id == co_captain_id, f"Player `{player_name}` is not Co-Captain."
    # Demote the player
    await this_team_player.set_field(TeamPlayerFields.is_co_captain, False)
    await db.table_team_player.update_team_player_record(this_team_player)
    # Success
    return True


async def is_captain(
    db: FullDatabase,
    team_player: PlayerRecord,
    needs_main: bool = False,
    needs_co: bool = False,
    assertive: bool = True,
    player_name: str = None,
) -> bool:
    """Check if a Player is a Captain


    Args:
        db (FullDatabase): The database
        player (PlayerRecord): The player
        needs_main (bool, optional): If the player needs to be the primary captain. Defaults to False.
        needs_co (bool, optional): If the player needs to be the co-captain. Defaults to False.
        assertive (bool, optional): If the function should assert. Defaults to True.
    """
    player_name = await team_player.get_field(PlayerFields.player_name)
    player_id = await team_player.get_field(PlayerFields.record_id)
    team_players = await db.table_team_player.get_team_player_records(
        player_id=player_id
    )
    assert team_players, f"Player is not on a team."
    team_player = team_players[0]
    is_captain = await team_player.get_field(TeamPlayerFields.is_captain)
    is_co_captain = await team_player.get_field(TeamPlayerFields.is_co_captain)
    if needs_main:
        if assertive:
            assert is_captain, f"Player is not the primary captain."
        return is_captain
    if needs_co:
        if assertive:
            assert is_co_captain, f"Player is not the co-captain."
        return is_co_captain
    is_any_captain = is_captain or is_co_captain
    if assertive:
        assert is_any_captain, f"Player is not a captain."
    return is_any_captain


### Team Invite ###


async def create_team_invite(
    db: FullDatabase,
    inviter: PlayerRecord,
    invitee: PlayerRecord,
):
    """Create a Team Invite"""
    # Verify the inviter and invitee are both registered players
    assert inviter, f"You must be registered as a player to invite players"
    assert invitee, f"Player not found."
    # Verify the inviter and invitee are in the same region
    inviter_player_id = await inviter.get_field(PlayerFields.record_id)
    invitee_player_id = await invitee.get_field(PlayerFields.record_id)
    inviter_region = await inviter.get_field(PlayerFields.region)
    invitee_region = await invitee.get_field(PlayerFields.region)
    assert_message = f"Player must be in the same region."
    assert inviter_region == invitee_region, assert_message
    # Verify the inviter is on a team
    inviter_team_players = await db.table_team_player.get_team_player_records(
        player_id=inviter_player_id
    )
    assert inviter_team_players, f"You must be on a Team to invite Players."
    # Verify inviter is a team captain
    inviter_team_player = inviter_team_players[0]
    is_captain = await inviter_team_player.get_field(TeamPlayerFields.is_captain)
    is_co_captain = await inviter_team_player.get_field(TeamPlayerFields.is_co_captain)
    assert is_captain or is_co_captain, "You must be a team captain to invite Players."
    # Cheak team invites
    team_id = await inviter_team_player.get_field(TeamPlayerFields.team_id)
    team_team_invites = await db.table_team_invite.get_team_invite_records(
        from_team_id=team_id
    )
    team_invite_count = len(team_team_invites)
    team_invite_max = constants.TEAM_INVITES_SEND_MAX
    assert team_invite_count < team_invite_max, f"Team has sent too many invites."
    # Verify the inviter has available invites
    inviter_sent_invites = await db.table_team_invite.get_team_invite_records(
        from_player_id=inviter_player_id
    )
    available_invites = constants.TEAM_INVITES_SEND_MAX - len(inviter_sent_invites)
    assert available_invites > 0, f"You have sent too many pending invites."
    # Check if invitee is already on a team
    invitee_team_players = await db.table_team_player.get_team_player_records(
        player_id=invitee_player_id
    )
    assert not invitee_team_players, f"Player is already on a team."
    # Check player invites
    invitee_team_invites = await db.table_team_invite.get_team_invite_records(
        to_player_id=invitee_player_id
    )
    available_invites = constants.TEAM_INVITES_RECEIVE_MAX - len(invitee_team_invites)
    assert available_invites > 0, f"Player has received too many invites."
    # Cheak team invites
    team_id = await inviter_team_player.get_field(TeamPlayerFields.team_id)
    team_team_invites = await db.table_team_invite.get_team_invite_records(
        from_team_id=team_id
    )
    team_invite_count = len(team_team_invites)
    team_invite_max = constants.TEAM_INVITES_SEND_MAX
    assert team_invite_count < team_invite_max, f"Team has sent too many invites."
    # Check for existing records to avoid duplication
    for invite in team_team_invites:
        invitee_id = await invite.get_field(TeamInviteFields.to_player_id)
        assert not invitee_id == invitee_player_id, f"Invite already sent."
    # Create the team invite
    team_name = await inviter_team_player.get_field(TeamPlayerFields.vw_team)
    inviter_player_name = await inviter.get_field(PlayerFields.player_name)
    invitee_player_name = await invitee.get_field(PlayerFields.player_name)
    new_team_invite = await db.table_team_invite.create_team_invite_record(
        from_team_id=team_id,
        from_player_id=inviter_player_id,
        to_player_id=invitee_player_id,
        from_team_name=team_name,
        from_player_name=inviter_player_name,
        to_player_name=invitee_player_name,
    )
    assert new_team_invite, f"Error: Could not create Team Invite."
    # Success
    return new_team_invite
