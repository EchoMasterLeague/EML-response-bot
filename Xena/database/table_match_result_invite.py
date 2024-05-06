from database.base_table import BaseTable
from database.database_core import CoreDatabase
from database.fields import MatchResultInviteFields
from database.records import MatchResultInviteRecord
from database.enums import InviteStatus, MatchResult, MatchType
import constants
import errors.database_errors as DbErrors
import gspread
import utils.general_helpers as general_helpers

"""
Match Result Invite Table
"""


class MatchResultInviteTable(BaseTable):
    """A class to manipulate the Match Result Invite table in the database"""

    _db: CoreDatabase
    _worksheet: gspread.Worksheet

    def __init__(self, db: CoreDatabase):
        """Initialize the Match Result Invite table class"""
        super().__init__(
            db,
            constants.LEAGUE_DB_TAB_MATCH_RESULT_INVITE,
            MatchResultInviteRecord,
            MatchResultInviteFields,
        )

    async def create_match_result_invite_record(
        self,
        match_id: str,
        inviter_team_id: str,
        inviter_player_id: str,
        invitee_team_id: str,
        match_outcome: MatchResult,
        match_type: MatchType,
        scores: list[list[int]],
        display_name: str,
    ) -> MatchResultInviteRecord:
        """Create a new Match Result Invite record

        Args:
            scores (list[list[int]]):
                scores[0] = [round_1_score_a, round_1_score_b]
                scores[1] = [round_2_score_a, round_2_score_b]
                scores[2] = [round_3_score_a, round_3_score_b]
        Note: the scores are from the perspective of the person sending the results, not necessarily the order of the teams on the match.
        """
        # Check for existing records to avoid duplication
        existing_record = await self.get_match_result_invite_records(
            inviter_team_id=inviter_team_id, invitee_team_id=invitee_team_id
        )
        if existing_record:
            raise DbErrors.EmlRecordAlreadyExists(
                f"Invite from team_id:'{inviter_team_id}' for team_id:'{invitee_team_id}' to confirm results already exists"
            )
        # Ensure there are 3 rounds
        if len(scores) < 3:
            scores = scores + [[None, None]] * (3 - len(scores))
        # Create the Invite record
        record_list = [None] * len(MatchResultInviteFields)
        record_list[MatchResultInviteFields.match_id] = match_id
        record_list[MatchResultInviteFields.match_type] = match_type
        record_list[MatchResultInviteFields.inviter_team_id] = inviter_team_id
        record_list[MatchResultInviteFields.inviter_player_id] = inviter_player_id
        record_list[MatchResultInviteFields.invitee_team_id] = invitee_team_id
        record_list[MatchResultInviteFields.invitee_player_id] = None
        record_list[MatchResultInviteFields.round_1_score_a] = scores[0][0]
        record_list[MatchResultInviteFields.round_1_score_b] = scores[0][1]
        record_list[MatchResultInviteFields.round_2_score_a] = scores[1][0]
        record_list[MatchResultInviteFields.round_2_score_b] = scores[1][1]
        record_list[MatchResultInviteFields.round_3_score_a] = scores[2][0]
        record_list[MatchResultInviteFields.round_3_score_b] = scores[2][1]
        record_list[MatchResultInviteFields.match_outcome] = match_outcome
        record_list[MatchResultInviteFields.invite_status] = InviteStatus.PENDING
        record_list[MatchResultInviteFields.display_name] = display_name
        new_record = await self.create_record(record_list, MatchResultInviteFields)
        # Insert the new record into the database
        await self.insert_record(new_record)
        return new_record

    async def update_match_result_invite_record(
        self, record: MatchResultInviteRecord
    ) -> None:
        """Update an existing Match Result Invite record"""
        await self.update_record(record)

    async def delete_match_result_invite_record(
        self, record: MatchResultInviteRecord
    ) -> None:
        """Delete an existing Match Result Invite record"""
        record_id = await record.get_field(MatchResultInviteFields.record_id)
        await self.delete_record(record_id)

    async def get_match_result_invite_records(
        self,
        record_id: str = None,
        inviter_team_id: str = None,
        inviter_player_id: str = None,
        invitee_team_id: str = None,
        invitee_player_id: str = None,
        invite_status: str = None,
    ) -> list[MatchResultInviteRecord]:
        """Get an existing Match Result Invite record"""
        if (
            record_id is None
            and inviter_team_id is None
            and invitee_team_id is None
            and inviter_player_id is None
            and invitee_player_id is None
            and invite_status is None
        ):
            raise ValueError(
                "At least one of the following parameters must be provided: record_id, inviter_team_id, invitee_team_id, inviter_player_id, invitee_player_id, status"
            )
        now = await general_helpers.epoch_timestamp()
        table = await self.get_table_data()
        existing_records: list[MatchResultInviteRecord] = []
        expired_records: list[MatchResultInviteRecord] = []
        for row in table:
            if table.index(row) == 0:
                continue
            # Check for expired records
            creation_epoch = await general_helpers.epoch_timestamp(
                row[MatchResultInviteFields.created_at]
            )
            duration_seconds = constants.MATCH_INVITES_EXPIRATION_DAYS * 60 * 60 * 24
            expiration_epoch = creation_epoch + duration_seconds
            if now > expiration_epoch:
                expired_record = MatchResultInviteRecord(row)
                expired_records.append(expired_record)
                continue
            # Check for matching records
            if (
                (
                    not record_id
                    or str(record_id).casefold()
                    == str(row[MatchResultInviteFields.record_id]).casefold()
                )
                and (
                    not inviter_team_id
                    or str(inviter_team_id).casefold()
                    == str(row[MatchResultInviteFields.inviter_team_id]).casefold()
                )
                and (
                    not invitee_team_id
                    or str(invitee_team_id).casefold()
                    == str(row[MatchResultInviteFields.invitee_team_id]).casefold()
                )
                and (
                    not inviter_player_id
                    or inviter_player_id.casefold()
                    == str(row[MatchResultInviteFields.inviter_player_id]).casefold()
                )
                and (
                    not invitee_player_id
                    or invitee_player_id.casefold()
                    == str(row[MatchResultInviteFields.invitee_player_id]).casefold()
                )
                and (
                    not invite_status
                    or invite_status.casefold()
                    == str(row[MatchResultInviteFields.status]).casefold()
                )
            ):
                existing_record = MatchResultInviteRecord(row)
                existing_records.append(existing_record)
        # Clean up expired records
        for expired_record in expired_records:
            await self.delete_match_result_invite_record(expired_record)
        return existing_records
