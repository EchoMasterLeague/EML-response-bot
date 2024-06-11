from database.base_table import BaseTable
from database.database_core import CoreDatabase
from database.enums import InviteStatus, MatchResult, MatchType
from database.fields import MatchResultInviteFields
from database.records import MatchResultInviteRecord
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
        match_type: MatchType,
        from_team_id: str,
        from_player_id: str,
        to_team_id: str,
        match_outcome: MatchResult,
        scores: list[tuple[int, int]],
        vw_from_team: str,
        vw_from_player: str,
        vw_to_team: str,
        expiration: int = None,
    ) -> MatchResultInviteRecord:
        """Create a new Match Result Invite record

        Args:
            scores (list[tubple[int, int]]):
                scores[0] = [round_1_score_a, round_1_score_b]
                scores[1] = [round_2_score_a, round_2_score_b]
                scores[2] = [round_3_score_a, round_3_score_b]
        Note: the scores are from the perspective of the person sending the results, not necessarily the order of the teams on the match.
        """
        # Check for existing records to avoid duplication
        existing_record = await self.get_match_result_invite_records(
            from_team_id=from_team_id, to_team_id=to_team_id, match_type=match_type
        )
        if existing_record:
            raise DbErrors.EmlRecordAlreadyExists(
                f"Invite from team '{vw_from_team}' for team '{vw_to_team}' to confirm results already exists for match type '{match_type}'"
            )
        # Prepare info for new record
        now = await general_helpers.epoch_timestamp()
        default_duration = constants.RESULT_INVITES_EXPIRATION_DAYS * 60 * 60 * 24
        expiration = expiration if expiration else now + default_duration
        expires_at = await general_helpers.iso_timestamp(expiration)
        # Ensure there are 3 rounds
        if len(scores) < 3:
            scores = scores + [(None, None)] * (3 - len(scores))
        # Create the new record
        record_list = [None] * len(MatchResultInviteFields)
        record_list[MatchResultInviteFields.match_id] = match_id
        record_list[MatchResultInviteFields.match_type] = match_type
        record_list[MatchResultInviteFields.from_team_id] = from_team_id
        record_list[MatchResultInviteFields.from_player_id] = from_player_id
        record_list[MatchResultInviteFields.to_team_id] = to_team_id
        record_list[MatchResultInviteFields.to_player_id] = None
        record_list[MatchResultInviteFields.round_1_score_a] = scores[0][0]
        record_list[MatchResultInviteFields.round_1_score_b] = scores[0][1]
        record_list[MatchResultInviteFields.round_2_score_a] = scores[1][0]
        record_list[MatchResultInviteFields.round_2_score_b] = scores[1][1]
        record_list[MatchResultInviteFields.round_3_score_a] = scores[2][0]
        record_list[MatchResultInviteFields.round_3_score_b] = scores[2][1]
        record_list[MatchResultInviteFields.match_outcome] = match_outcome
        record_list[MatchResultInviteFields.invite_status] = InviteStatus.PENDING
        record_list[MatchResultInviteFields.invite_expires_at] = expires_at
        record_list[MatchResultInviteFields.vw_from_team] = vw_from_team
        record_list[MatchResultInviteFields.vw_from_player] = vw_from_player
        record_list[MatchResultInviteFields.vw_to_team] = vw_to_team
        record_list[MatchResultInviteFields.vw_to_player] = None
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
        match_type: str = None,
        from_team_id: str = None,
        from_player_id: str = None,
        to_team_id: str = None,
        to_player_id: str = None,
        invite_status: str = None,
    ) -> list[MatchResultInviteRecord]:
        """Get an existing Match Result Invite record"""
        if (
            record_id is None
            and match_type is None
            and from_team_id is None
            and to_team_id is None
            and from_player_id is None
            and to_player_id is None
            and invite_status is None
        ):
            raise ValueError(
                f"At least one of the following parameters must be provided: 'record_id', 'match_type', 'from_team_id', 'to_team_id', 'from_player_id', 'to_player_id', 'invite_status'"
            )
        now = await general_helpers.epoch_timestamp()
        table = await self.get_table_data()
        existing_records: list[MatchResultInviteRecord] = []
        expired_records: list[MatchResultInviteRecord] = []
        for row in table:
            # Skip the header row
            if table.index(row) == 0:
                continue
            # Check for expired records
            expiration_epoch = await general_helpers.epoch_timestamp(
                row[MatchResultInviteFields.invite_expires_at]
            )
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
                    not match_type
                    or match_type.casefold()
                    == str(row[MatchResultInviteFields.match_type]).casefold()
                )
                and (
                    not from_team_id
                    or str(from_team_id).casefold()
                    == str(row[MatchResultInviteFields.from_team_id]).casefold()
                )
                and (
                    not to_team_id
                    or str(to_team_id).casefold()
                    == str(row[MatchResultInviteFields.to_team_id]).casefold()
                )
                and (
                    not from_player_id
                    or from_player_id.casefold()
                    == str(row[MatchResultInviteFields.from_player_id]).casefold()
                )
                and (
                    not to_player_id
                    or to_player_id.casefold()
                    == str(row[MatchResultInviteFields.to_player_id]).casefold()
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
