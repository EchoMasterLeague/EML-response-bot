from database.base_table import BaseTable
from database.database_core import CoreDatabase
from database.enums import MatchType, MatchStatus
from database.fields import MatchFields
from database.records import MatchRecord
import constants
import errors.database_errors as DbErrors
import gspread
import utils.general_helpers as general_helpers


"""
Match Table
"""


class MatchTable(BaseTable):
    """A class to manipulate the Match table in the database"""

    _db: CoreDatabase
    _worksheet: gspread.Worksheet

    def __init__(self, db: CoreDatabase):
        """Initialize the Match Table class"""
        super().__init__(db, constants.LEAGUE_DB_TAB_MATCH, MatchRecord, MatchFields)

    async def create_match_record(
        self,
        team_a_id: str,
        team_b_id: str,
        match_epoch: int,
        match_type: MatchType,
        vw_team_a: str,
        vw_team_b: str,
    ) -> MatchRecord:
        """Create a new Match record"""
        match_week = await general_helpers.season_week(match_epoch)
        # Check for existing records to avoid duplication
        existing_records = await self.get_match_records(
            team_a_id=team_a_id,
            team_b_id=team_b_id,
            match_week=match_week,
            match_type=match_type,
            match_status=MatchStatus.PENDING.value,
        )
        if not existing_records:
            existing_records = await self.get_match_records(
                team_a_id=team_b_id,
                team_b_id=team_a_id,
                match_week=match_week,
                match_type=match_type,
                match_status=MatchStatus.PENDING.value,
            )
        if existing_records:
            raise DbErrors.EmlRecordAlreadyExists(
                f"Pending Match of type '{match_type}' between '{vw_team_a}' and '{vw_team_b}' already exists for week '{match_week}'"
            )
        # Prepare info for new record
        match_date = await general_helpers.eml_date(match_epoch)
        match_time = await general_helpers.eml_time(match_epoch)
        # Create the Match record
        match_timestamp = await general_helpers.iso_timestamp(match_epoch)
        record_list = [None] * len(MatchFields)
        record_list[MatchFields.match_timestamp] = match_timestamp
        record_list[MatchFields.match_week] = match_week
        record_list[MatchFields.match_type] = match_type
        record_list[MatchFields.team_a_id] = team_a_id
        record_list[MatchFields.team_b_id] = team_b_id
        record_list[MatchFields.outcome] = None
        record_list[MatchFields.match_date] = match_date
        record_list[MatchFields.match_time_et] = match_time
        record_list[MatchFields.round_1_score_a] = None
        record_list[MatchFields.round_1_score_b] = None
        record_list[MatchFields.round_2_score_a] = None
        record_list[MatchFields.round_2_score_b] = None
        record_list[MatchFields.round_3_score_a] = None
        record_list[MatchFields.round_3_score_b] = None
        record_list[MatchFields.match_status] = MatchStatus.PENDING.value
        record_list[MatchFields.vw_team_a] = vw_team_a
        record_list[MatchFields.vw_team_b] = vw_team_b
        new_record = await self.create_record(record_list, MatchFields)
        # Insert the new record into the database
        await self.insert_record(new_record)
        return new_record

    async def update_match_record(self, record: MatchRecord) -> None:
        """Update an existing Player record"""
        await self.update_record(record)

    async def delete_match_record(self, record: MatchRecord) -> None:
        """Delete an existing Player record"""
        record_id = await record.get_field(MatchFields.record_id)
        await self.delete_record(record_id)

    async def get_match_records(
        self,
        record_id: str = None,
        match_week: str = None,
        match_type: str = None,
        team_a_id: str = None,
        team_b_id: str = None,
        outcome: str = None,
        match_status: str = None,
    ) -> list[MatchRecord]:
        """Get existing Match records"""
        if (
            record_id is None
            and match_week is None
            and match_type is None
            and team_a_id is None
            and team_b_id is None
            and outcome is None
            and match_status is None
        ):
            raise ValueError(
                "At least one of the following parameters must be provided: record_id, match_week, match_type, team_a_id, team_b_id, outcome, match_status"
            )
        table = await self.get_table_data()
        existing_records: list[MatchRecord] = []
        for row in table:
            # Skip header row
            if table.index(row) == 0:
                continue
            # Check for matching records
            if (
                (
                    not record_id
                    or str(record_id).casefold()
                    == str(row[MatchFields.record_id]).casefold()
                )
                and (
                    not match_week
                    or str(match_week).casefold()
                    == str(row[MatchFields.match_week]).casefold()
                )
                and (
                    not match_type
                    or str(match_type).casefold()
                    == str(row[MatchFields.match_type]).casefold()
                )
                and (
                    not team_a_id
                    or str(team_a_id).casefold()
                    == str(row[MatchFields.team_a_id]).casefold()
                )
                and (
                    not team_b_id
                    or str(team_b_id).casefold()
                    == str(row[MatchFields.team_b_id]).casefold()
                )
                and (
                    not outcome
                    or str(outcome).casefold()
                    == str(row[MatchFields.outcome]).casefold()
                )
                and (
                    not match_status
                    or str(match_status).casefold()
                    == str(row[MatchFields.match_status]).casefold()
                )
            ):
                existing_records.append(MatchRecord(row))
        return existing_records
