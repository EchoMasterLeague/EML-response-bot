from database.base_table import BaseTable
from database.database_core import CoreDatabase
from database.fields import TeamPlayerFields
from database.records import TeamPlayerRecord
import constants
import errors.database_errors as DbErrors
import gspread
import logging

logger = logging.getLogger(__name__)


"""
TeamPlayer Table
"""


class TeamPlayerTable(BaseTable):
    """A class to manipulate the TeamPlayer table in the database"""

    _db: CoreDatabase
    _worksheet: gspread.Worksheet

    def __init__(self, db: CoreDatabase):
        """Initialize the TeamPlayer Table class"""
        super().__init__(
            db, constants.LEAGUE_DB_TAB_TEAM_PLAYER, TeamPlayerRecord, TeamPlayerFields
        )

    async def create_team_player_record(
        self,
        team_id: str,
        player_id: str,
        team_name: str,
        player_name: str,
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
        # Create the new record
        record_list = [None] * len(TeamPlayerFields)
        record_list[TeamPlayerFields.team_id] = team_id
        record_list[TeamPlayerFields.player_id] = player_id
        record_list[TeamPlayerFields.is_captain] = is_captain
        record_list[TeamPlayerFields.is_co_captain] = is_co_captain
        record_list[TeamPlayerFields.vw_team] = team_name
        record_list[TeamPlayerFields.vw_player] = player_name
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
        # Walk the table
        table = await self.get_table_data()
        existing_records = []
        for row in table[1:]:  # skip header row
            # Check for matched records
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
                # Add matched record
                existing_record = TeamPlayerRecord(row)
                existing_records.append(existing_record)
        # Return matched records
        return existing_records
