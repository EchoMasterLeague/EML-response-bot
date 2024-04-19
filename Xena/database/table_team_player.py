from database.base_table import BaseFields, BaseRecord, BaseTable
from database.database import Database
from enum import IntEnum, verify, EnumCheck, StrEnum
from typing import Type
import constants
import errors.database_errors as DbErrors
import gspread


@verify(EnumCheck.UNIQUE, EnumCheck.CONTINUOUS)
class TeamPlayerFields(IntEnum):
    """Lookup for column numbers of fields in this table

    note: `gspread` uses 1-based indexes, these are 0-based.
    """

    record_id = BaseFields.record_id
    created_at = BaseFields.created_at
    updated_at = BaseFields.updated_at
    team_id = 3  # The id of the team
    player_id = 4  # The id of the player
    is_captain = 5  # Whether or not the player is the captain of the team
    is_co_captain = 6  # Whether or not the player is a co-captain of the team


@verify(EnumCheck.UNIQUE)
class Bool(StrEnum):
    """Lookup for truthy values in the TeamPlayer table"""

    TRUE = "Yes"
    FALSE = "No"


class TeamPlayerRecord(BaseRecord):
    """Record class for this table"""

    _fields: Type[TeamPlayerFields]
    _data_dict: dict

    def __init__(
        self,
        data_list: list[int | float | str | None],
        fields: Type[TeamPlayerFields] = TeamPlayerFields,
    ):
        """Create a record from a list of data (e.g. from `gsheets`)"""
        super().__init__(data_list, fields)
        # Conversion / Validation
        ## Is Captain
        is_captain = data_list[TeamPlayerFields.is_captain.value]
        is_captain = (
            True
            if (
                is_captain == True
                or str(is_captain).casefold() == str(Bool.TRUE).casefold()
            )
            else False
        )
        self._data_dict[TeamPlayerFields.is_captain.name] = is_captain
        ## Is Co-Captain
        is_co_captain = data_list[TeamPlayerFields.is_co_captain.value]
        is_co_captain = (
            True
            if (
                is_co_captain == True
                or str(is_co_captain).casefold() == str(Bool.TRUE).casefold()
            )
            else False
        )
        self._data_dict[TeamPlayerFields.is_co_captain.name] = is_co_captain

    async def to_list(self) -> list[int | float | str | None]:
        """Return the record as a list of data (e.g. for `gsheets`)"""
        data_list = await super().to_list()
        # Conversion
        is_captain = self._data_dict[TeamPlayerFields.is_captain.name]
        data_list[TeamPlayerFields.is_captain.value] = (
            Bool.TRUE if is_captain else Bool.FALSE
        )
        is_co_captain = self._data_dict[TeamPlayerFields.is_co_captain.name]
        data_list[TeamPlayerFields.is_co_captain.value] = (
            Bool.TRUE if is_co_captain else Bool.FALSE
        )
        return data_list


class TeamPlayerTable(BaseTable):
    """A class to manipulate the TeamPlayer table in the database"""

    _db: Database
    _worksheet: gspread.Worksheet

    def __init__(self, db: Database):
        """Initialize the TeamPlayer Action class"""
        super().__init__(db, constants.LEAGUE_DB_TAB_TEAM_PLAYER, TeamPlayerRecord)

    async def create_team_player_record(
        self,
        team_id: str,
        player_id: str,
        is_captain: bool = False,
        is_co_captain: bool = False,
    ) -> TeamPlayerRecord:
        """Create a new TeamPlayer record"""
        # Check for existing records to avoid duplication
        existing_record = await self.get_team_player_records(
            team_id=team_id, player_id=player_id
        )
        if existing_record:
            raise DbErrors.EmlRecordAlreadyExists(
                f"TeamPlayer '{team_id}' '{player_id}' already exists"
            )
        # Create the TeamPlayer record
        record_list = [None] * len(TeamPlayerFields)
        record_list[TeamPlayerFields.team_id] = team_id
        record_list[TeamPlayerFields.player_id] = player_id
        record_list[TeamPlayerFields.is_captain] = is_captain
        record_list[TeamPlayerFields.is_co_captain] = is_co_captain
        new_record = await self.create_record(record_list, TeamPlayerFields)
        # Insert the new record into the database
        await self.insert_record(new_record)
        return new_record

    async def update_team_player_record(self, record: TeamPlayerRecord) -> None:
        """Update an existing Player record"""
        await self.update_record(record)

    async def delete_team_player_record(self, record: TeamPlayerRecord) -> None:
        """Delete an existing Player record"""
        record_id = await record.get_field(TeamPlayerFields.record_id)
        await self.delete_record(record_id)

    async def get_team_player_records(
        self, record_id: str = None, team_id: str = None, player_id: str = None
    ) -> list[TeamPlayerRecord]:
        """Get existing TeamPlayer records"""
        if record_id is None and team_id is None and player_id is None:
            raise ValueError(
                "At least one of 'record_id', 'team_id', or 'player_id' is required"
            )
        table = await self.get_table_data()
        existing_records: list[TeamPlayerRecord] = []
        for row in table:
            if (
                (
                    not record_id
                    or str(record_id).casefold()
                    == str(row[TeamPlayerFields.record_id]).casefold()
                )
                and (
                    not team_id
                    or str(team_id).casefold()
                    == str(row[TeamPlayerFields.team_id]).casefold()
                )
                and (
                    not player_id
                    or str(player_id).casefold()
                    == str(row[TeamPlayerFields.player_id]).casefold()
                )
            ):
                existing_records.append(TeamPlayerRecord(row))
        return existing_records
