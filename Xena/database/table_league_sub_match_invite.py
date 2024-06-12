from database.base_table import BaseTable
from database.database_core import CoreDatabase
from database.fields import LeagueSubMatchInviteFields
from database.enums import InviteStatus
from database.records import LeagueSubMatchInviteRecord
import constants
import errors.database_errors as DbErrors
import gspread
from utils import general_helpers

"""
LeagueSubMatchInvite Table
"""


class LeagueSubMatchInviteTable(BaseTable):
    """A class to manipulate the LeagueSubMatchInvite table in the database"""

    _db: CoreDatabase
    _worksheet: gspread.Worksheet

    def __init__(self, db: CoreDatabase):
        """Initialize the LeagueSubMatchInvite Table class"""
        super().__init__(
            db,
            constants.LEAGUE_DB_TAB_LEAGUE_SUB_MATCH_INVITE,
            LeagueSubMatchInviteRecord,
            LeagueSubMatchInviteFields,
        )

    async def create_league_sub_match_invite_record(
        self,
        match_id: str,
        vw_team: str,
        team_id: str,
        vw_sub: str,
        sub_player_id: str,
        vw_captain: str,
        captain_player_id: str,
    ) -> LeagueSubMatchInviteRecord:
        """Create a new LeagueSubMatchInvite record"""
        # Check for existing records to avoid duplication
        existing_records = await self.get_league_sub_match_invite_records(
            match_id=match_id, sub_player_id=sub_player_id, team_id=team_id
        )
        if existing_records:
            raise DbErrors.EmlRecordAlreadyExists(
                f"LeagueSubMatchInvite for `{vw_sub}` playing for `{vw_team}` already exists"
            )
        # prepare info for new record
        expiration_iso = await general_helpers.iso_timestamp(
            await general_helpers.epoch_timestamp()
            + constants.INVITES_TO_SUB_EXPIRATION_DAYS * 60 * 60 * 24
        )
        # Create the new record
        record_list = [None] * len(LeagueSubMatchInviteFields)
        record_list[LeagueSubMatchInviteFields.match_id] = match_id
        record_list[LeagueSubMatchInviteFields.sub_player_id] = sub_player_id
        record_list[LeagueSubMatchInviteFields.team_id] = team_id
        record_list[LeagueSubMatchInviteFields.captain_player_id] = captain_player_id
        record_list[LeagueSubMatchInviteFields.invite_expires_at] = expiration_iso
        record_list[LeagueSubMatchInviteFields.invite_status] = InviteStatus.PENDING
        record_list[LeagueSubMatchInviteFields.vw_sub] = vw_sub
        record_list[LeagueSubMatchInviteFields.vw_team] = vw_team
        record_list[LeagueSubMatchInviteFields.vw_captain] = vw_captain
        new_record = await self.create_record(record_list, LeagueSubMatchInviteFields)
        # Insert the new record into the database
        await self.insert_record(new_record)
        return new_record

    async def update_league_sub_match_invite_record(
        self, record: LeagueSubMatchInviteRecord
    ) -> None:
        """Update an existing LeagueSubMatchInvite record"""
        await self.update_record(record)

    async def delete_league_sub_match_invite_record(
        self, record: LeagueSubMatchInviteRecord
    ) -> None:
        """Delete an existing LeagueSubMatchInvite record"""
        record_id = await record.get_field(LeagueSubMatchInviteFields.record_id)
        await self.delete_record(record_id)

    async def get_league_sub_match_invite_records(
        self,
        record_id: str = None,
        match_id: str = None,
        sub_player_id: str = None,
        team_id: str = None,
        invite_status: InviteStatus = None,
    ) -> list[LeagueSubMatchInviteRecord]:
        """Get existing LeagueSubMatchInvite records"""
        if (
            record_id is None
            and match_id is None
            and sub_player_id is None
            and team_id is None
            and invite_status is None
        ):
            raise ValueError(
                "At least one of `record_id`, `match_id`, `player_id`, `team_id` or `invite_status` must be provided"
            )
        now = await general_helpers.epoch_timestamp()
        table = await self.get_table_data()
        existing_records = []
        expired_records = []
        for row in table:
            # Skip the header row
            if table.index(row) == 0:
                continue
            # Check for expired records
            expiration_epoch = await general_helpers.epoch_timestamp(
                row[LeagueSubMatchInviteFields.invite_expires_at]
            )
            if now > expiration_epoch:
                expired_records.append(LeagueSubMatchInviteRecord(row))
                continue
            # Check for matching records
            if (
                (
                    not record_id
                    or str(record_id).casefold()
                    == str(row[LeagueSubMatchInviteFields.record_id]).casefold()
                )
                and (
                    not match_id
                    or str(match_id).casefold()
                    == str(row[LeagueSubMatchInviteFields.match_id]).casefold()
                )
                and (
                    not sub_player_id
                    or sub_player_id.casefold()
                    == str(row[LeagueSubMatchInviteFields.sub_player_id]).casefold()
                )
                and (
                    not team_id
                    or team_id.casefold()
                    == str(row[LeagueSubMatchInviteFields.team_id]).casefold()
                )
                and (
                    not invite_status
                    or invite_status == row[LeagueSubMatchInviteFields.invite_status]
                )
            ):
                existing_records.append(LeagueSubMatchInviteRecord(row))
        # Delete expired records
        for expired_record in expired_records:
            await self.delete_league_sub_match_invite_record(expired_record)
        return existing_records
