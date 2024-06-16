from database.base_table import BaseTable
from database.database_core import CoreDatabase
from database.fields import LeagueSubMatchFields
from database.records import LeagueSubMatchRecord
import constants
import errors.database_errors as DbErrors
import gspread

"""
LeagueSubMatch Table
"""


class LeagueSubMatchTable(BaseTable):
    """A class to manipulate the LeagueSubMatch table in the database"""

    _db: CoreDatabase
    _worksheet: gspread.Worksheet

    def __init__(self, db: CoreDatabase):
        """Initialize the LeagueSubMatch Table class"""
        super().__init__(
            db,
            constants.LEAGUE_DB_TAB_LEAGUE_SUB_MATCH,
            LeagueSubMatchRecord,
            LeagueSubMatchFields,
        )

    async def create_league_sub_match_record(
        self,
        match_id: str,
        player_id: str,
        team_id: str,
        vw_player: str = None,
        vw_team: str = None,
        vw_timestamp: str = None,
        vw_type: str = None,
        vw_team_a: str = None,
        vw_team_b: str = None,
        vw_winner: str = None,
    ) -> LeagueSubMatchRecord:
        """Create a new LeagueSubMatch record"""
        # Check for existing records to avoid duplication
        existing_records = await self.get_league_sub_match_records(
            match_id=match_id, player_id=player_id, team_id=team_id
        )
        if existing_records:
            raise DbErrors.EmlRecordAlreadyExists(
                f"LeagueSubMatch for `{vw_player}` playing for `{vw_team}` in `{vw_type}` match on `{vw_timestamp}` (match_id: `{match_id}`) already exists"
            )
        # Create the new record
        record_list = [None] * len(LeagueSubMatchFields)
        record_list[LeagueSubMatchFields.match_id] = match_id
        record_list[LeagueSubMatchFields.player_id] = player_id
        record_list[LeagueSubMatchFields.team_id] = team_id
        record_list[LeagueSubMatchFields.vw_player] = vw_player
        record_list[LeagueSubMatchFields.vw_team] = vw_team
        record_list[LeagueSubMatchFields.vw_timestamp] = vw_timestamp
        record_list[LeagueSubMatchFields.vw_type] = vw_type
        record_list[LeagueSubMatchFields.vw_team_a] = vw_team_a
        record_list[LeagueSubMatchFields.vw_team_b] = vw_team_b
        record_list[LeagueSubMatchFields.vw_winner] = vw_winner
        new_record = await self.create_record(record_list, LeagueSubMatchFields)
        # Insert the new record into the database
        await self.insert_record(new_record)
        return new_record

    async def update_league_sub_match_record(
        self, record: LeagueSubMatchRecord
    ) -> None:
        """Update an existing LeagueSubMatch record"""
        await self.update_record(record)

    async def delete_league_sub_match_record(
        self, record: LeagueSubMatchRecord
    ) -> None:
        """Delete an existing LeagueSubMatch record"""
        record_id = await record.get_field(LeagueSubMatchFields.record_id)
        await self.delete_record(record_id)

    async def get_league_sub_match_records(
        self,
        record_id: str = None,
        match_id: str = None,
        player_id: str = None,
        team_id: str = None,
    ) -> list[LeagueSubMatchRecord]:
        """Get existing LeagueSubMatch records"""
        # Walk the table
        table = await self.get_table_data()
        existing_records = []
        for row in table[1:]:  # skip header row
            # Check for matched record
            if (
                (
                    not record_id
                    or str(record_id).casefold()
                    == str(row[LeagueSubMatchFields.record_id]).casefold()
                )
                and (
                    not match_id
                    or str(match_id).casefold()
                    == str(row[LeagueSubMatchFields.match_id]).casefold()
                )
                and (
                    not player_id
                    or player_id.casefold()
                    == str(row[LeagueSubMatchFields.player_id]).casefold()
                )
                and (
                    not team_id
                    or team_id.casefold()
                    == str(row[LeagueSubMatchFields.team_id]).casefold()
                )
            ):
                # Add matched record
                existing_record = LeagueSubMatchRecord(row)
                existing_records.append(existing_record)
        # Return matched records
        return existing_records
