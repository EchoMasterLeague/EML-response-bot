from database.base_table import BaseFields, BaseRecord, BaseTable
from database.database import Database
from enum import IntEnum, StrEnum, verify, EnumCheck
from typing import Type
import constants
import errors.database_errors as DbErrors
import gspread
import utils.database_helpers as helpers


@verify(EnumCheck.UNIQUE, EnumCheck.CONTINUOUS)
class TeamFields(IntEnum):
    """Lookup for column numbers of fields in this table

    note: `gspread` uses 1-based indexes, these are 0-based.
    """

    RECORD_ID = BaseFields.RECORD_ID
    CREATED_AT = BaseFields.CREATED_AT
    UPDATED_AT = BaseFields.UPDATED_AT
    TEAM_NAME = 3  # The name of the team
    STATUS = 4  # The status of the team


@verify(EnumCheck.UNIQUE)
class TeamStatus(StrEnum):
    """Lookup for status values in the Team table"""

    ACTIVE = "Active"  # The team is active
    INACTIVE = "Inactive"  # The team is inactive


class TeamRecord(BaseRecord):
    """Record class for this table"""

    _fields: Type[TeamFields]
    _data_dict: dict

    def __init__(self, data_list: list[int | float | str | None]):
        """Create a record from a list of data (e.g. from `gsheets`)"""
        super().__init__(TeamFields, data_list)
        # Conversion / Validaton
        ## Status
        status = self._data_dict[TeamFields.STATUS.name]
        status_list = [s.value for s in TeamStatus]
        for allowed_status in status_list:
            if str(status).casefold() == allowed_status.casefold():
                self._data_dict[TeamFields.STATUS.name] = allowed_status
                break
        if self._data_dict[TeamFields.STATUS.name] not in status_list:
            raise DbErrors.EmlTeamStatusNotFound(
                f"Status '{status}' not available. Available Statuses: {status_list}"
            )


class TeamTable(BaseTable):
    """A class to manipulate the Team table in the database"""

    _db: Database
    _worksheet: gspread.Worksheet

    def __init__(self, db: Database):
        """Initialize the Team Action class"""
        super().__init__(db, constants.LEAGUE_DB_TAB_TEAM, TeamRecord)

    async def create_team(self, team_name: str) -> TeamRecord:
        """Create a new Team record"""
        # Check for existing records to avoid duplication
        existing_record = await self.get_team(team_name=team_name)
        if existing_record:
            raise DbErrors.EmlTeamAlreadyExists(f"Team '{team_name}' already exists")
        # Create the Team record
        record_list = [None] * len(TeamFields)
        record_list[TeamFields.TEAM_NAME] = team_name
        record_list[TeamFields.STATUS] = TeamStatus.ACTIVE
        new_record = self.create_record(TeamRecord, record_list)
        # Insert the new record into the database
        await self.insert_record(new_record)
        return new_record

    async def update_team(self, record: TeamRecord) -> None:
        """Update an existing Team record"""
        await self.update_record(record)

    async def delete_team(self, record: TeamRecord) -> None:
        """Delete an existing Team record"""
        record_id = record.get_field(TeamFields.RECORD_ID)
        await self.delete_record(record_id)

    async def get_team(
        self, record_id: str = None, team_name: str = None
    ) -> TeamRecord:
        """Get an existing Team record"""
        if record_id is None and team_name is None:
            raise DbErrors.EmlTeamNotFound(
                "At least one of 'record_id' or 'team_name' is required"
            )
        table = self.get_table_data()
        for row in table:
            if (
                not record_id
                or str(record_id).casefold()
                == str(row[TeamFields.RECORD_ID]).casefold()
            ) and (
                not team_name
                or str(team_name).casefold()
                == str(row[TeamFields.RECORD_ID]).casefold()
            ):
                existing_record = TeamRecord(row)
                return existing_record
        raise DbErrors.EmlTeamNotFound("Team not found")
