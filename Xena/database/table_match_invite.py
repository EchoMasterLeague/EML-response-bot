from database.base_table import BaseTable
from database.database_core import CoreDatabase
from database.enums import InviteStatus
from database.fields import MatchInviteFields
from database.records import MatchInviteRecord
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
        match_epoch: int,
        from_team_id: str,
        from_player_id: str,
        to_team_id: str,
        vw_from_team: str,
        vw_to_team: str,
        vw_from_player: str,
        expiration: int = None,
    ) -> MatchInviteRecord:
        """Create a new Match Invite record"""
        # Check for existing records to avoid duplication
        existing_record = await self.get_match_invite_records(
            from_team_id=from_team_id, to_team_id=to_team_id
        )
        if existing_record:
            raise DbErrors.EmlRecordAlreadyExists(
                f"Invite from team `{vw_from_team}` to play team `{vw_to_team}` already exists"
            )
        # Prepare info for new record
        now = await general_helpers.epoch_timestamp()
        default_invite_duration = (
            constants.INVITES_TO_MATCH_EXPIRATION_DAYS * 60 * 60 * 24
        )
        default_expiration_epoch = now + default_invite_duration
        expiration = expiration if expiration else default_expiration_epoch
        expires_at = await general_helpers.iso_timestamp(expiration)
        match_timestamp = await general_helpers.iso_timestamp(match_epoch)
        match_date = await general_helpers.eml_date(match_epoch)
        match_time_et = await general_helpers.eml_time(match_epoch)
        # Create the new record
        record_list = [None] * len(MatchInviteFields)
        record_list[MatchInviteFields.from_team_id] = from_team_id
        record_list[MatchInviteFields.to_team_id] = to_team_id
        record_list[MatchInviteFields.from_player_id] = from_player_id
        record_list[MatchInviteFields.to_player_id] = None
        record_list[MatchInviteFields.invite_status] = InviteStatus.PENDING
        record_list[MatchInviteFields.invite_expires_at] = expires_at
        record_list[MatchInviteFields.match_timestamp] = match_timestamp
        record_list[MatchInviteFields.match_date] = match_date
        record_list[MatchInviteFields.match_time_et] = match_time_et
        record_list[MatchInviteFields.match_type] = match_type
        record_list[MatchInviteFields.vw_from_team] = vw_from_team
        record_list[MatchInviteFields.vw_from_player] = vw_from_player
        record_list[MatchInviteFields.vw_to_team] = vw_to_team
        record_list[MatchInviteFields.vw_to_player] = None
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
        from_team_id: str = None,
        from_player_id: str = None,
        to_team_id: str = None,
        to_player_id: str = None,
        invite_status: str = None,
    ) -> list[MatchInviteRecord]:
        """Get an existing Match Invite records"""
        if (
            record_id is None
            and from_team_id is None
            and to_team_id is None
            and from_player_id is None
            and to_player_id is None
            and invite_status is None
        ):
            raise ValueError(
                "At least one of the following parameters must be provided: record_id, from_team_id, to_team_id, from_player_id, to_player_id, invite_status"
            )
        now = await general_helpers.epoch_timestamp()
        table = await self.get_table_data()
        existing_records: list[MatchInviteRecord] = []
        expired_records: list[MatchInviteRecord] = []
        for row in table:
            # Skip the header row
            if table.index(row) == 0:
                continue
            # Check for expired records
            expiration_epoch = await general_helpers.epoch_timestamp(
                row[MatchInviteFields.invite_expires_at]
            )
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
                    not from_team_id
                    or str(from_team_id).casefold()
                    == str(row[MatchInviteFields.from_team_id]).casefold()
                )
                and (
                    not to_team_id
                    or str(to_team_id).casefold()
                    == str(row[MatchInviteFields.to_team_id]).casefold()
                )
                and (
                    not from_player_id
                    or from_player_id.casefold()
                    == str(row[MatchInviteFields.from_player_id]).casefold()
                )
                and (
                    not to_player_id
                    or to_player_id.casefold()
                    == str(row[MatchInviteFields.to_player_id]).casefold()
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
