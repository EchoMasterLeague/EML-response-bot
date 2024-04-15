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

    RECORD_ID = BaseFields.RECORD_ID
    CREATED_AT = BaseFields.CREATED_AT
    UPDATED_AT = BaseFields.UPDATED_AT
    TEAM_ID = 3  # The id of the team
    PLAYER_ID = 4  # The id of the player
    IS_CAPTAIN = 5  # Whether or not the player is the captain of the team
    IS_CO_CAPTAIN = 6  # Whether or not the player is a co-captain of the team


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
        is_captain = data_list[TeamPlayerFields.IS_CAPTAIN.value]
        is_captain = (
            True
            if (
                is_captain == True
                or str(is_captain).casefold() == str(Bool.TRUE).casefold()
            )
            else False
        )
        self._data_dict[TeamPlayerFields.IS_CAPTAIN.name] = is_captain
        ## Is Co-Captain
        is_co_captain = data_list[TeamPlayerFields.IS_CO_CAPTAIN.value]
        is_co_captain = (
            True
            if (
                is_co_captain == True
                or str(is_co_captain).casefold() == str(Bool.TRUE).casefold()
            )
            else False
        )
        self._data_dict[TeamPlayerFields.IS_CO_CAPTAIN.name] = is_co_captain

    async def to_list(self) -> list[int | float | str | None]:
        """Return the record as a list of data (e.g. for `gsheets`)"""
        data_list = await super().to_list()
        # Conversion
        is_captain = self._data_dict[TeamPlayerFields.IS_CAPTAIN.name]
        data_list[TeamPlayerFields.IS_CAPTAIN.value] = (
            Bool.TRUE if is_captain else Bool.FALSE
        )
        is_co_captain = self._data_dict[TeamPlayerFields.IS_CO_CAPTAIN.name]
        data_list[TeamPlayerFields.IS_CO_CAPTAIN.value] = (
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
        try:
            existing_record = await self.get_team_player_records(
                team_id=team_id, player_id=player_id
            )
        except DbErrors.EmlTeamPlayerNotFound:
            existing_record = None
        if existing_record:
            raise DbErrors.EmlTeamPlayerAlreadyExists(
                f"TeamPlayer '{team_id}' '{player_id}' already exists"
            )
        # Create the TeamPlayer record
        record_list = [None] * len(TeamPlayerFields)
        record_list[TeamPlayerFields.PLAYER_ID] = player_id
        record_list[TeamPlayerFields.IS_CAPTAIN] = is_captain
        record_list[TeamPlayerFields.IS_CO_CAPTAIN] = is_co_captain
        new_record = await self.create_record(record_list, TeamPlayerFields)
        # Insert the new record into the database
        await self.insert_record(new_record)
        return new_record

    async def update_team_player_record(self, record: TeamPlayerRecord) -> None:
        """Update an existing Player record"""
        self.update_record(record)

    async def delete_team_player_record(self, record: TeamPlayerRecord) -> None:
        """Delete an existing Player record"""
        record_id = await record.get_field(TeamPlayerFields.RECORD_ID)
        self.delete_record(record_id)

    async def get_team_player_records(
        self, record_id: str = None, team_id: str = None, player_id: str = None
    ) -> list[TeamPlayerRecord]:
        """Get existing TeamPlayer records"""
        if record_id is None and team_id is None and player_id is None:
            raise DbErrors.EmlTeamPlayerNotFound(
                "At least one of 'record_id', 'team_id', or 'player_id' is required"
            )
        table = await self.get_table_data()
        existing_records: list[TeamPlayerRecord] = []
        for row in table:
            if (
                (
                    not record_id
                    or str(record_id).casefold()
                    == str(row[TeamPlayerFields.RECORD_ID]).casefold()
                )
                and (
                    not team_id
                    or str(team_id).casefold()
                    == str(row[TeamPlayerFields.TEAM_ID]).casefold()
                )
                and (
                    not player_id
                    or str(player_id).casefold()
                    == str(row[TeamPlayerFields.PLAYER_ID]).casefold()
                )
            ):
                existing_records.append(TeamPlayerRecord(row))
        if existing_records:
            return existing_records
        raise DbErrors.EmlTeamPlayerNotFound("TeamPlayer not found")
