from database.base_table import BaseTable
from database.database_core import CoreDatabase
from database.enums import InviteStatus
from database.fields import TeamInviteFields
from database.records import TeamInviteRecord
import constants
import errors.database_errors as DbErrors
import gspread
import utils.general_helpers as general_helpers
import logging

logger = logging.getLogger(__name__)

"""
Team Invite Table
"""


class TeamInviteTable(BaseTable):
    """A class to manipulate the Invite table in the database"""

    _db: CoreDatabase
    _worksheet: gspread.Worksheet

    def __init__(self, db: CoreDatabase):
        """Initialize the Invite Table class"""
        super().__init__(
            db, constants.LEAGUE_DB_TAB_TEAM_INVITE, TeamInviteRecord, TeamInviteFields
        )

    async def create_team_invite_record(
        self,
        from_team_id: str,
        from_player_id: str,
        to_player_id: str,
        from_team_name: str,
        from_player_name: str,
        to_player_name: str,
    ) -> TeamInviteRecord:
        """Create a new Invite record"""
        # Check for existing records to avoid duplication
        existing_record = await self.get_team_invite_records(
            from_team_id=from_team_id, to_player_id=to_player_id
        )
        if existing_record:
            raise DbErrors.EmlRecordAlreadyExists(
                f"Invite for '{to_player_name}' to join '{from_team_name}' already exists"
            )
        # prepare info for new record
        now = await general_helpers.epoch_timestamp()
        expiration_epoch = (
            now + constants.INVITES_TO_TEAM_EXPIRATION_DAYS * 60 * 60 * 24
        )
        expiration_iso = await general_helpers.iso_timestamp(expiration_epoch)
        # Create the new record
        record_list = [None] * len(TeamInviteFields)
        record_list[TeamInviteFields.from_team_id] = from_team_id
        record_list[TeamInviteFields.from_player_id] = from_player_id
        record_list[TeamInviteFields.to_player_id] = to_player_id
        record_list[TeamInviteFields.invite_status] = InviteStatus.PENDING
        record_list[TeamInviteFields.invite_expires_at] = expiration_iso
        record_list[TeamInviteFields.vw_team] = from_team_name
        record_list[TeamInviteFields.vw_from_player] = from_player_name
        record_list[TeamInviteFields.vw_to_player] = to_player_name
        new_record = await self.create_record(record_list, TeamInviteFields)
        # Insert the new record into the database
        await self.insert_record(new_record)
        return new_record

    async def update_team_invite_record(self, record: TeamInviteRecord) -> None:
        """Update an existing Invite record"""
        await self.update_record(record)

    async def delete_team_invite_record(self, record: TeamInviteRecord) -> None:
        """Delete an existing Invite record"""
        record_id = await record.get_field(TeamInviteFields.record_id)
        await self.delete_record(record_id)

    async def get_team_invite_records(
        self,
        record_id: str = None,
        from_team_id: str = None,
        from_player_id: str = None,
        to_player_id: str = None,
    ) -> list[TeamInviteRecord]:
        """Get an existing Invite record
        Note: Since this has to walk the whole table anyway, this is also used to clean up expired records
        """
        # Prepare for expired records
        now = await general_helpers.epoch_timestamp()
        expired_records = []
        # Walk the table
        table = await self.get_table_data()
        existing_records = []
        for row in table[1:]:  # skip header row
            # Check for expired record
            expiration_epoch = await general_helpers.epoch_timestamp(
                row[TeamInviteFields.invite_expires_at]
            )
            if now > expiration_epoch:
                expired_record = TeamInviteRecord(row)
                expired_records.append(expired_record)
                continue
            # Check for matched records
            if (
                (
                    not record_id
                    or str(record_id).casefold()
                    == str(row[TeamInviteFields.record_id]).casefold()
                )
                and (
                    not from_team_id
                    or str(from_team_id).casefold()
                    == str(row[TeamInviteFields.from_team_id]).casefold()
                )
                and (
                    not from_player_id
                    or from_player_id.casefold()
                    == str(row[TeamInviteFields.from_player_id]).casefold()
                )
                and (
                    not to_player_id
                    or to_player_id.casefold()
                    == str(row[TeamInviteFields.to_player_id]).casefold()
                )
            ):
                # Add matched record
                existing_record = TeamInviteRecord(row)
                existing_records.append(existing_record)
        # Delete expired records
        for expired_record in expired_records:
            await self.delete_team_invite_record(expired_record)
        # Return matched records
        return existing_records
