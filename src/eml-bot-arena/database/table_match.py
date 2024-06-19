from database.base_table import BaseTable
from database.database_core import CoreDatabase
from database.enums import MatchType, MatchStatus
from database.fields import MatchFields
from database.records import MatchRecord
import constants
import errors.database_errors as DbErrors
import gspread
from utils import general_helpers, match_helpers
import logging

logger = logging.getLogger(__name__)


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
        match_epoch: int,
        team_a_id: str,
        team_b_id: str,
        vw_team_a: str = None,
        vw_team_b: str = None,
        vw_sub_a: str = None,
        vw_sub_b: str = None,
        match_status: MatchStatus = MatchStatus.PENDING,
        match_type: MatchType = MatchType.ASSIGNED,
        outcome: MatchStatus = None,
        scores: list[list[int, int]] = None,
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
        if existing_records:
            raise DbErrors.EmlRecordAlreadyExists(
                f"Pending Match of type '{match_type}' between '{vw_team_a}' and '{vw_team_b}' already exists for week '{match_week}'"
            )
        # Prepare info for new record
        match_date = await general_helpers.eml_date(match_epoch)
        match_time = await general_helpers.eml_time(match_epoch)
        if match_type:
            match_type = await match_helpers.get_normalized_match_type(match_type)
            if not match_type:
                raise ValueError("Invalid match type")
        if scores:
            is_valid_scores = await match_helpers.is_score_structure_valid(scores)
            if not is_valid_scores:
                raise ValueError("Invalid scores structure")
        else:
            scores = [[None, None], [None, None], [None, None]]
        if outcome:
            if not scores:
                raise ValueError("Scores must be provided to set the outcome")
            is_valid_outcome = await match_helpers.is_outcome_consistent_with_scores(
                outcome, scores
            )
            if not is_valid_outcome:
                raise ValueError("Scores and outcome do not match")
        if match_status:
            match_status = await match_helpers.get_normalized_match_status(match_status)
            if not match_status:
                raise ValueError("Invalid match status")
        else:
            match_status = MatchStatus.PENDING
        # Create the new record
        match_timestamp = await general_helpers.iso_timestamp(match_epoch)
        record_list = [None] * len(MatchFields)
        record_list[MatchFields.match_timestamp] = match_timestamp
        record_list[MatchFields.match_date] = match_date
        record_list[MatchFields.match_time_et] = match_time
        record_list[MatchFields.match_week] = match_week
        record_list[MatchFields.team_a_id] = team_a_id
        record_list[MatchFields.team_b_id] = team_b_id
        record_list[MatchFields.vw_team_a] = vw_team_a
        record_list[MatchFields.vw_team_b] = vw_team_b
        record_list[MatchFields.vw_sub_a] = vw_sub_a
        record_list[MatchFields.vw_sub_b] = vw_sub_b
        record_list[MatchFields.match_type] = match_type
        record_list[MatchFields.match_status] = match_status
        record_list[MatchFields.outcome] = outcome
        record_list[MatchFields.round_1_score_a] = scores[0][0]
        record_list[MatchFields.round_1_score_b] = scores[0][1]
        record_list[MatchFields.round_2_score_a] = scores[1][0]
        record_list[MatchFields.round_2_score_b] = scores[1][1]
        record_list[MatchFields.round_3_score_a] = scores[2][0]
        record_list[MatchFields.round_3_score_b] = scores[2][1]
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
        match_timestamp: str = None,
    ) -> list[MatchRecord]:
        """Get existing Match records"""
        table = await self.get_table_data()
        existing_records = []
        for row in table[1:]:  # skip header row
            # Check for matched records
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
                and (
                    not match_timestamp
                    or str(match_timestamp).casefold()
                    == str(row[MatchFields.match_timestamp]).casefold()
                )
            ):
                # Add matched record
                existing_record = MatchRecord(row)
                existing_records.append(existing_record)
        # Return matched records
        return existing_records
