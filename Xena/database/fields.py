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
class InviteFields(IntEnum):
    """Lookup for column numbers of fields in the Invite table"""

    record_id = BaseFields.record_id
    created_at = BaseFields.created_at
    updated_at = BaseFields.updated_at
    team_id = 3  # Record ID of the Team
    inviter_player_id = 4  # Record ID of the Invite sending the invite
    invitee_player_id = 5  # Record ID of the Invite receiving the invite


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
