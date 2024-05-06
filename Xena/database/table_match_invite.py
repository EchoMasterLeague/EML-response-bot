from database.base_table import BaseTable
from database.database_core import CoreDatabase
from database.fields import MatchInviteFields
from database.records import MatchInviteRecord
from database.enums import InviteStatus
import constants
import errors.database_errors as DbErrors
import gspread
import utils.general_helpers as general_helpers

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
        match_type: str,
        inviter_team_id: str,
        inviter_player_id: str,
        invitee_team_id: str,
        match_epoch: int,
        display_name: str = None,
    ) -> MatchInviteRecord:
        """Create a new Match Invite record"""
        # Check for existing records to avoid duplication
        existing_record = await self.get_match_invite_records(
            inviter_team_id=inviter_team_id, invitee_team_id=invitee_team_id
        )
        if existing_record:
            raise DbErrors.EmlRecordAlreadyExists(
                f"Invite for team_id:'{inviter_team_id}' to play team_id:'{invitee_team_id}' already exists"
            )
        # Get relevant data
        match_timestamp = await general_helpers.iso_timestamp(match_epoch)
        match_date = await general_helpers.eml_date(match_epoch)
        match_time_et = await general_helpers.eml_time(match_epoch)
        # Create the Match Invite record
        record_list = [None] * len(MatchInviteFields)
        record_list[MatchInviteFields.inviter_team_id] = inviter_team_id
        record_list[MatchInviteFields.invitee_team_id] = invitee_team_id
        record_list[MatchInviteFields.inviter_player_id] = inviter_player_id
        record_list[MatchInviteFields.invitee_player_id] = None
        record_list[MatchInviteFields.invite_status] = InviteStatus.PENDING
        record_list[MatchInviteFields.match_timestamp] = match_timestamp
        record_list[MatchInviteFields.match_date] = match_date
        record_list[MatchInviteFields.match_time_et] = match_time_et
        record_list[MatchInviteFields.display_name] = display_name
        record_list[MatchInviteFields.match_type] = match_type
        new_record = await self.create_record(record_list, MatchInviteFields)
        # Insert the new record into the database
        await self.insert_record(new_record)
        return new_record

    async def update_match_invite_record(self, record: MatchInviteRecord) -> None:
        """Update an existing Match Invite record"""
        await self.update_record(record)

    async def delete_match_invite_record(self, record: MatchInviteRecord) -> None:
        """Delete an existing Match Invite record"""
        record_id = await record.get_field(MatchInviteFields.record_id)
        await self.delete_record(record_id)

    async def get_match_invite_records(
        self,
        record_id: str = None,
        inviter_team_id: str = None,
        inviter_player_id: str = None,
        invitee_team_id: str = None,
        invitee_player_id: str = None,
        invite_status: str = None,
    ) -> list[MatchInviteRecord]:
        """Get an existing Match Invite records"""
        if (
            record_id is None
            and inviter_team_id is None
            and invitee_team_id is None
            and inviter_player_id is None
            and invitee_player_id is None
            and invite_status is None
        ):
            raise ValueError(
                "At least one of the following parameters must be provided: record_id, inviter_team_id, invitee_team_id, inviter_player_id, invitee_player_id, invite_status"
            )
        now = await general_helpers.epoch_timestamp()
        table = await self.get_table_data()
        existing_records: list[MatchInviteRecord] = []
        expired_records: list[MatchInviteRecord] = []
        for row in table:
            if table.index(row) == 0:
                continue
            # Check for expired records
            creation_epoch = await general_helpers.epoch_timestamp(
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
                    not invite_status
                    or invite_status.casefold()
                    == str(row[MatchInviteFields.invite_status]).casefold()
                )
            ):
                existing_record = MatchInviteRecord(row)
                existing_records.append(existing_record)
        # Clean up expired records
        for expired_record in expired_records:
            await self.delete_match_invite_record(expired_record)
        return existing_records