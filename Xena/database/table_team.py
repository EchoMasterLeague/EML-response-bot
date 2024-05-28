from database.base_table import BaseTable
from database.database_core import CoreDatabase
from database.fields import TeamFields
from database.records import TeamRecord
from database.enums import TeamStatus
import constants
import errors.database_errors as DbErrors
import gspread

"""
Team Table
"""


class TeamTable(BaseTable):
    """A class to manipulate the Team table in the database"""

    _db: CoreDatabase
    _worksheet: gspread.Worksheet

    def __init__(self, db: CoreDatabase):
        """Initialize the Team Table class"""
        super().__init__(db, constants.LEAGUE_DB_TAB_TEAM, TeamRecord, TeamFields)

    async def create_team_record(self, team_name: str, vw_region: str) -> TeamRecord:
        """Create a new Team record"""
        # Check for existing records to avoid duplication
        existing_record = await self.get_team_record(team_name=team_name)
        if existing_record:
            raise DbErrors.EmlRecordAlreadyExists(f"Team '{team_name}' already exists")
        # Create the Team record
        record_list = [None] * len(TeamFields)
        record_list[TeamFields.team_name] = team_name
        record_list[TeamFields.status] = TeamStatus.INACTIVE
        record_list[TeamFields.vw_region] = vw_region
        new_record = await self.create_record(record_list, TeamFields)
        # Insert the new record into the database
        await self.insert_record(new_record)
        return new_record

    async def update_team_record(self, record: TeamRecord) -> None:
        """Update an existing Team record"""
        await self.update_record(record)

    async def delete_team_record(self, record: TeamRecord) -> None:
        """Delete an existing Team record"""
        record_id = await record.get_field(TeamFields.record_id)
        await self.delete_record(record_id)

    async def get_team_record(
        self, record_id: str = None, team_name: str = None
    ) -> TeamRecord:
        """Get an existing Team record"""
        if record_id is None and team_name is None:
            raise ValueError("At least one of 'record_id' or 'team_name' is required")
        table = await self.get_table_data()
        for row in table:
            if table.index(row) == 0:
                continue
            if (
                not record_id
                or str(record_id).casefold()
                == str(row[TeamFields.record_id]).casefold()
            ) and (
                not team_name
                or str(team_name).casefold()
                == str(row[TeamFields.team_name]).casefold()
            ):
                existing_record = TeamRecord(row)
                return existing_record
        return None
