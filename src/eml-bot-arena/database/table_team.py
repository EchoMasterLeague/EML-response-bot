from database.base_table import BaseTable
from database.database_core import CoreDatabase
from database.enums import TeamStatus
from database.fields import TeamFields
from database.records import TeamRecord
import constants
import errors.database_errors as DbErrors
import gspread
import logging

logger = logging.getLogger(__name__)

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
        existing_records = await self.get_team_records(team_name=team_name)
        if existing_records:
            raise DbErrors.EmlRecordAlreadyExists(f"Team '{team_name}' already exists")
        # Create the new record
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

    async def get_team_records(
        self, record_id: str = None, team_name: str = None
    ) -> list[TeamRecord]:
        """Get an existing Team record"""
        # Walk the table
        table = await self.get_table_data()
        existing_records = []
        for row in table[1:]:  # skip header row
            # Check for matched records
            if (
                not record_id
                or str(record_id).casefold()
                == str(row[TeamFields.record_id]).casefold()
            ) and (
                not team_name
                or str(team_name).casefold()
                == str(row[TeamFields.team_name]).casefold()
            ):
                # Add matched record
                existing_record = TeamRecord(row)
                existing_records.append(existing_record)
        # Return matched records
        return existing_records
