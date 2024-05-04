from database.base_table import BaseTable
from database.database_core import CoreDatabase
from database.fields import MatchInviteFields
from database.records import MatchInviteRecord
from database.enums import InviteStatus
import constants
import errors.database_errors as DbErrors
import gspread
import utils.database_helpers as helpers

"""
Match Invite Table
"""


class MatchInviteTable(BaseTable):
    """A class to manipulate the Match Invite table in the database"""

    _db: CoreDatabase
    _worksheet: gspread.Worksheet

    def __init__(self, db: CoreDatabase):
        """Initialize the Match Invite table class"""
        super().__init__(
            db,
            constants.LEAGUE_DB_TAB_MATCH_INVITE,
            MatchInviteRecord,
            MatchInviteFields,
        )

    async def create_match_invite_record(
        self,
        inviter_team_id: str,
        inviter_player_id: str,
        invitee_team_id: str,
        invitee_player_id: str,
    ) -> MatchInviteRecord:
        """Create a new Match Invite record"""
        # Check for existing records to avoid duplication
        existing_record = await self.get_match_invite_records(
            team_id=inviter_team_id, invitee_player_id=invitee_player_id
        )
        if existing_record:
            raise DbErrors.EmlRecordAlreadyExists(
                f"Invite for invite_id:'{invitee_player_id}' to join team_id:'{inviter_team_id}' already exists"
            )
        # Create the Invite record
        record_list = [None] * len(MatchInviteFields)
        record_list[MatchInviteFields.inviter_team_id] = inviter_team_id
        record_list[MatchInviteFields.invitee_team_id] = invitee_team_id
        record_list[MatchInviteFields.inviter_player_id] = inviter_player_id
        record_list[MatchInviteFields.invitee_player_id] = invitee_player_id
        record_list[MatchInviteFields.status] = InviteStatus.PENDING
        new_record = await self.create_record(record_list, MatchInviteFields)
        # Insert the new record into the database
        await self.insert_record(new_record)
        return new_record

    async def update_match_invite_record(self, record: MatchInviteRecord) -> None:
        """Update an existing Invite record"""
        await self.update_record(record)

    async def delete_match_invite_record(self, record: MatchInviteRecord) -> None:
        """Delete an existing Invite record"""
        record_id = await record.get_field(MatchInviteFields.record_id)
        await self.delete_record(record_id)

    async def get_match_invite_records(
        self,
        record_id: str = None,
        inviter_team_id: str = None,
        inviter_player_id: str = None,
        invitee_team_id: str = None,
        invitee_player_id: str = None,
        status: str = None,
    ) -> list[MatchInviteRecord]:
        """Get an existing Invite record"""
        if (
            record_id is None
            and inviter_team_id is None
            and invitee_team_id is None
            and inviter_player_id is None
            and invitee_player_id is None
            and status is None
        ):
            raise ValueError(
                "At least one of the following parameters must be provided: record_id, inviter_team_id, invitee_team_id, inviter_player_id, invitee_player_id, status"
            )
        now = await helpers.epoch_timestamp()
        table = await self.get_table_data()
        existing_records: list[MatchInviteRecord] = []
        expired_records: list[MatchInviteRecord] = []
        for row in table:
            if table.index(row) == 0:
                continue
            # Check for expired records
            creation_epoch = await helpers.epoch_timestamp(
                row[MatchInviteFields.created_at]
            )
            duration_seconds = constants.MATCH_INVITES_EXPIRATION_DAYS * 60 * 60 * 24
            expiration_epoch = creation_epoch + duration_seconds
            if now > expiration_epoch:
                expired_record = MatchInviteRecord(row)
                expired_records.append(expired_record)
                continue
            # Check for matching records
            if (
                (
                    not record_id
                    or str(record_id).casefold()
                    == str(row[MatchInviteFields.record_id]).casefold()
                )
                and (
                    not inviter_team_id
                    or str(inviter_team_id).casefold()
                    == str(row[MatchInviteFields.inviter_team_id]).casefold()
                )
                and (
                    not invitee_team_id
                    or str(invitee_team_id).casefold()
                    == str(row[MatchInviteFields.invitee_team_id]).casefold()
                )
                and (
                    not inviter_player_id
                    or inviter_player_id.casefold()
                    == str(row[MatchInviteFields.inviter_player_id]).casefold()
                )
                and (
                    not invitee_player_id
                    or invitee_player_id.casefold()
                    == str(row[MatchInviteFields.invitee_player_id]).casefold()
                )
                and (
                    not status
                    or status.casefold()
                    == str(row[MatchInviteFields.status]).casefold()
                )
            ):
                existing_record = MatchInviteRecord(row)
                existing_records.append(existing_record)
        # Clean up expired records
        for expired_record in expired_records:
            await self.delete_match_invite_record(expired_record)
        return existing_records
