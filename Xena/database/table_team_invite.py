from database.base_table import BaseTable
from database.database_core import CoreDatabase
from database.fields import TeamInviteFields
from database.records import TeamInviteRecord
import constants
import errors.database_errors as DbErrors
import gspread
import utils.database_helpers as helpers

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
        self, team_id: str, inviter_player_id: str, invitee_player_id: str
    ) -> TeamInviteRecord:
        """Create a new Invite record"""
        # Check for existing records to avoid duplication
        existing_record = await self.get_team_invite_records(
            team_id=team_id, invitee_player_id=invitee_player_id
        )
        if existing_record:
            raise DbErrors.EmlRecordAlreadyExists(
                f"Invite for invite_id:'{invitee_player_id}' to join team_id:'{team_id}' already exists"
            )
        # Create the Invite record
        record_list = [None] * len(TeamInviteFields)
        record_list[TeamInviteFields.team_id] = team_id
        record_list[TeamInviteFields.inviter_player_id] = inviter_player_id
        record_list[TeamInviteFields.invitee_player_id] = invitee_player_id
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
        team_id: str = None,
        inviter_player_id: str = None,
        invitee_player_id: str = None,
    ) -> list[TeamInviteRecord]:
        """Get an existing Invite record"""
        if (
            record_id is None
            and team_id is None
            and inviter_player_id is None
            and invitee_player_id is None
        ):
            raise ValueError(
                "At least one of the following parameters must be provided: record_id, team_id, inviter_player_id, invitee_player_id"
            )
        now = await helpers.epoch_timestamp()
        table = await self.get_table_data()
        existing_records: list[TeamInviteRecord] = []
        expired_records: list[TeamInviteRecord] = []
        for row in table:
            if table.index(row) == 0:
                continue
            # Check for expired records
            creation_epoch = await helpers.epoch_timestamp(
                row[TeamInviteFields.created_at]
            )
            duration_seconds = constants.TEAM_INVITES_EXPIRATION_DAYS * 60 * 60 * 24
            expiration_epoch = creation_epoch + duration_seconds
            if now > expiration_epoch:
                expired_record = TeamInviteRecord(row)
                expired_records.append(expired_record)
                continue
            # Check for matching records
            if (
                (
                    not record_id
                    or str(record_id).casefold()
                    == str(row[TeamInviteFields.record_id]).casefold()
                )
                and (
                    not team_id
                    or str(team_id).casefold()
                    == str(row[TeamInviteFields.team_id]).casefold()
                )
                and (
                    not inviter_player_id
                    or inviter_player_id.casefold()
                    == str(row[TeamInviteFields.inviter_player_id]).casefold()
                )
                and (
                    not invitee_player_id
                    or invitee_player_id.casefold()
                    == str(row[TeamInviteFields.invitee_player_id]).casefold()
                )
            ):
                existing_record = TeamInviteRecord(row)
                existing_records.append(existing_record)
        # Delete expired records
        for expired_record in expired_records:
            await self.delete_team_invite_record(expired_record)
        return existing_records
