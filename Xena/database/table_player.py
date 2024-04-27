from database.base_table import BaseFields, BaseRecord, BaseTable
from database.database import Database
from enum import IntEnum, verify, EnumCheck, StrEnum
from typing import Type
import constants
import errors.database_errors as DbErrors
import gspread

"""
Player Table
"""


@verify(EnumCheck.UNIQUE, EnumCheck.CONTINUOUS)
class PlayerFields(IntEnum):
    """Lookup for column numbers of fields in this table

    note: `gspread` uses 1-based indexes, these are 0-based.
    """

    record_id = BaseFields.record_id
    created_at = BaseFields.created_at
    updated_at = BaseFields.updated_at
    discord_id = 3  # Numeric Discord ID of the player
    player_name = 4  # Display Name of the player
    region = 5  # Region of the player


@verify(EnumCheck.UNIQUE)
class Regions(StrEnum):
    """Lookup for Region values in the Player table"""

    NA = "NA"  # North America
    EU = "EU"  # Europe
    OCE = "OCE"  # Oceanic


class PlayerRecord(BaseRecord):
    """Record class for this table"""

    _fields: Type[PlayerFields]
    _data_dict: dict

    def __init__(
        self,
        data_list: list[int | float | str | None],
        fields: Type[PlayerFields] = PlayerFields,
    ):
        """Create a record from a list of data (e.g. from `gsheets`)"""
        super().__init__(data_list, fields)
        # Conversion / Validaton
        ## Discord ID
        discord_id = self._data_dict[PlayerFields.discord_id.name]
        self._data_dict[PlayerFields.discord_id.name] = str(discord_id)
        ## Region
        region = self._data_dict[PlayerFields.region.name]
        region_list = [r.value for r in Regions]
        for allowed_region in region_list:
            if str(region).casefold() == allowed_region.casefold():
                self._data_dict[PlayerFields.region.name] = allowed_region
                break
        if self._data_dict[PlayerFields.region.name] not in region_list:
            raise DbErrors.EmlRegionNotFound(
                f"Region '{region}' not available. Available Regions: {region_list}"
            )


class PlayerTable(BaseTable):
    """A class to manipulate the Player table in the database"""

    _db: Database
    _worksheet: gspread.Worksheet

    def __init__(self, db: Database):
        """Initialize the Player Action class"""
        super().__init__(db, constants.LEAGUE_DB_TAB_PLAYER, PlayerRecord)

    async def create_player_record(
        self, discord_id: str, player_name: str, region: str
    ) -> PlayerRecord:
        """Create a new Player record"""
        # Check for existing records to avoid duplication
        existing_record = await self.get_player_record(
            discord_id=discord_id, player_name=player_name
        )
        if existing_record:
            raise DbErrors.EmlRecordAlreadyExists(
                f"Player '{player_name}' already exists"
            )
        # Create the Player record
        record_list = [None] * len(PlayerFields)
        record_list[PlayerFields.discord_id] = discord_id
        record_list[PlayerFields.player_name] = player_name
        record_list[PlayerFields.region] = region
        new_record = await self.create_record(record_list, PlayerFields)
        # Insert the new record into the database
        await self.insert_record(new_record)
        return new_record

    async def update_player_record(self, record: PlayerRecord) -> None:
        """Update an existing Player record"""
        await self.update_record(record)

    async def delete_player_record(self, record: PlayerRecord) -> None:
        """Delete an existing Player record"""
        record_id = await record.get_field(PlayerFields.record_id)
        await self.delete_record(record_id)

    async def get_player_record(
        self, record_id: str = None, discord_id: str = None, player_name: str = None
    ) -> PlayerRecord:
        """Get an existing Player record"""
        if record_id is None and discord_id is None and player_name is None:
            raise ValueError(
                "At least one of 'record_id', 'discord_id', or 'player_name' is required"
            )
        table = await self.get_table_data()
        for row in table:
            if (
                (
                    not record_id
                    or str(record_id).casefold()
                    == str(row[PlayerFields.record_id]).casefold()
                )
                and (
                    not discord_id
                    or str(discord_id).casefold()
                    == str(row[PlayerFields.discord_id]).casefold()
                )
                and (
                    not player_name
                    or player_name.casefold()
                    == str(row[PlayerFields.player_name]).casefold()
                )
            ):
                existing_record = PlayerRecord(row)
                return existing_record
        return None

    async def get_players_by_region(self, region: str) -> list[PlayerRecord]:
        """Get all players from a specific region"""
        # Validate the region
        is_region_allowed = False
        allowed_region_list = [r.value for r in Regions]
        for allowed_region in allowed_region_list:
            if region.casefold() == allowed_region.casefold():
                region = allowed_region
                is_region_allowed = True
                break
        if not is_region_allowed:
            raise DbErrors.EmlRegionNotFound(
                f"Region '{region}' not available. Available Regions: {allowed_region_list}"
            )
        # Get the players from the region
        table = await self.get_table_data()
        players = []
        for row in table:
            if region == row[PlayerFields.region]:
                player = PlayerRecord(row)
                players.append(player)
        return players
