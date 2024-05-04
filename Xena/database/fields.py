from enum import IntEnum, EnumCheck, StrEnum, verify


@verify(EnumCheck.UNIQUE, EnumCheck.CONTINUOUS)
class BaseFields(IntEnum):
    """Lookup for column numbers of fields in all tables

    note: `gspread` uses 1-based indexes, these are 0-based.
    These must be the first three fields in ALL tables.
    """

    record_id = 0  # The unique identifier for the record
    created_at = 1  # The ISO 8601 timestamp of when the record was created
    updated_at = 2  # The ISO 8601 timestamp of when the record was last updated


@verify(EnumCheck.UNIQUE, EnumCheck.CONTINUOUS)
class ExampleFields(IntEnum):
    """Lookup for column numbers of fields in the Example table"""

    record_id = BaseFields.record_id
    created_at = BaseFields.created_at
    updated_at = BaseFields.updated_at
    example_a = 3  # EXAMPLE_A description
    example_b = 4  # EXAMPLE_B description


@verify(EnumCheck.UNIQUE, EnumCheck.CONTINUOUS)
class CommandLockFields(IntEnum):
    """Lookup for column numbers of fields in the CommandLock table"""

    record_id = BaseFields.record_id
    created_at = BaseFields.created_at
    updated_at = BaseFields.updated_at
    command_name = 3  # Name of bot command
    is_allowed = 4  # Whether or not the command can be used


@verify(EnumCheck.UNIQUE, EnumCheck.CONTINUOUS)
class CooldownFields(IntEnum):
    """Lookup for column numbers of fields in the Cooldown table"""

    record_id = BaseFields.record_id
    created_at = BaseFields.created_at
    updated_at = BaseFields.updated_at
    player_id = 3  # Record ID of the player
    expires_at = 4  # Timestamp when the cooldown expires


@verify(EnumCheck.UNIQUE, EnumCheck.CONTINUOUS)
class MatchInviteFields(IntEnum):
    """Lookup for column numbers of fields in the MatchInvite table"""

    record_id = BaseFields.record_id
    created_at = BaseFields.created_at
    updated_at = BaseFields.updated_at
    inviter_team_id = 3  # Record ID of the Team sending the match invite
    inviter_player_id = 4  # Record ID of the player sending the match invite
    invitee_team_id = 5  # Record ID of the Team receiving the match invite
    invitee_player_id = 6  # Record ID of the player responding to the match invite
    match_date = 7  # Date of the match
    match_time = 8  # Time of the match
    invite_status = 9  # Status of the match invite


@verify(EnumCheck.UNIQUE, EnumCheck.CONTINUOUS)
class MatchFields(IntEnum):
    """Lookup for column numbers of fields in the Match table"""

    record_id = BaseFields.record_id
    created_at = BaseFields.created_at
    updated_at = BaseFields.updated_at
    match_timestamp = 3  # Date of the match
    match_week = 4  # Week of the match YYYYWW
    match_type = 5  # Type of the match
    team_a_id = 6  # Record ID of the first team
    outome = 7  # Result of the match
    team_b_id = 8  # Record ID of the second team
    match_date = 9  # Date of the match
    match_time = 10  # Time of the match
    match_status = 11  # Status of the match
    round_1_score_a = 12  # Score of the first team in the first round
    round_1_score_b = 13  # Score of the second team in the first round
    round_2_score_a = 14  # Score of the first team in the second round
    round_2_score_b = 15  # Score of the second team in the second round
    round_3_score_a = 16  # Score of the first team in the third round
    round_3_score_b = 17  # Score of the second team in the third round


@verify(EnumCheck.UNIQUE, EnumCheck.CONTINUOUS)
class MatchResultInviteFields(IntEnum):
    """Lookup for column numbers of fields in the MatchResultInvite table"""

    record_id = BaseFields.record_id
    created_at = BaseFields.created_at
    updated_at = BaseFields.updated_at
    match_id = 3  # Record ID of the Match
    inviter_team_id = 4  # Record ID of the Team sending the match result invite
    inviter_player_id = 5  # Record ID of the player sending the match result invite
    invitee_team_id = 6  # Record ID of the Team receiving the match result invite
    invitee_player_id = 7  # Record ID of the player responding to the match result
    round_1_score_a = 8  # Score of the first team in the first round
    round_1_score_b = 9  # Score of the second team in the first round
    round_2_score_a = 10  # Score of the first team in the second round
    round_2_score_b = 11  # Score of the second team in the second round
    round_3_score_a = 12  # Score of the first team in the third round
    round_3_score_b = 13  # Score of the second team in the third round
    match_outcome = 14  # Result of the match
    match_type = 15  # Type of the match
    invite_status = 16  # Status of the match result invite


@verify(EnumCheck.UNIQUE, EnumCheck.CONTINUOUS)
class PlayerFields(IntEnum):
    """Lookup for column numbers of fields in the Player table"""

    record_id = BaseFields.record_id
    created_at = BaseFields.created_at
    updated_at = BaseFields.updated_at
    discord_id = 3  # Numeric Discord ID of the player
    player_name = 4  # Display Name of the player
    region = 5  # Region of the player


@verify(EnumCheck.UNIQUE, EnumCheck.CONTINUOUS)
class TeamInviteFields(IntEnum):
    """Lookup for column numbers of fields in the TeamInvite table"""

    record_id = BaseFields.record_id
    created_at = BaseFields.created_at
    updated_at = BaseFields.updated_at
    team_id = 3  # Record ID of the Team
    inviter_player_id = 4  # Record ID of the Player sending the TeamInvite
    invitee_player_id = 5  # Record ID of the Player receiving the TeamInvite


@verify(EnumCheck.UNIQUE, EnumCheck.CONTINUOUS)
class TeamPlayerFields(IntEnum):
    """Lookup for column numbers of fields in the TeamPlayer table"""

    record_id = BaseFields.record_id
    created_at = BaseFields.created_at
    updated_at = BaseFields.updated_at
    team_id = 3  # The id of the team
    player_id = 4  # The id of the player
    is_captain = 5  # Whether or not the player is the captain of the team
    is_co_captain = 6  # Whether or not the player is a co-captain of the team


@verify(EnumCheck.UNIQUE, EnumCheck.CONTINUOUS)
class TeamFields(IntEnum):
    """Lookup for column numbers of fields in the Team table"""

    record_id = BaseFields.record_id
    created_at = BaseFields.created_at
    updated_at = BaseFields.updated_at
    team_name = 3  # The name of the team
    status = 4  # The status of the team
