from database.base_table import BaseFields, BaseRecord, BaseTable
from database.database import Database
from enum import IntEnum, verify, EnumCheck, StrEnum
from typing import Type
import constants
import errors.database_errors as DbErrors
import gspread

"""
Team Table
"""


@verify(EnumCheck.UNIQUE, EnumCheck.CONTINUOUS)
class InviteFields(IntEnum):
    """Lookup for column numbers of fields in this table

    note: `gspread` uses 1-based indexes, these are 0-based.
    """

    record_id = BaseFields.record_id
    created_at = BaseFields.created_at
    updated_at = BaseFields.updated_at
    team_id = 3  # Record ID of the Team
    inviter_player_id = 4  # Record ID of the Invite sending the invite
    invitee_player_id = 5  # Record ID of the Invite receiving the invite


class InviteRecord(BaseRecord):
    """Record class for this table"""

    _fields: Type[InviteFields]
    _data_dict: dict

    def __init__(
        self,
        data_list: list[int | float | str | None],
        fields: Type[InviteFields] = InviteFields,
    ):
        """Create a record from a list of data (e.g. from `gsheets`)"""
        super().__init__(data_list, fields)


class InviteTable(BaseTable):
    """A class to manipulate the Invite table in the database"""

    _db: Database
    _worksheet: gspread.Worksheet

    def __init__(self, db: Database):
        """Initialize the Invite Table class"""
        super().__init__(db, constants.LEAGUE_DB_TAB_INVITE, InviteRecord)

    async def create_invite_record(
        self, team_id: str, inviter_player_id: str, invitee_player_id: str
    ) -> InviteRecord:
        """Create a new Invite record"""
        # Check for existing records to avoid duplication
        existing_record = await self.get_invite_records(
            team_id=team_id, invitee_player_id=invitee_player_id
        )
        if existing_record:
            raise DbErrors.EmlRecordAlreadyExists(
                f"Invite for invite_id:'{invitee_player_id}' to join team_id:'{team_id}' already exists"
            )
        # Create the Invite record
        record_list = [None] * len(InviteFields)
        record_list[InviteFields.team_id] = team_id
        record_list[InviteFields.inviter_player_id] = inviter_player_id
        record_list[InviteFields.invitee_player_id] = invitee_player_id
        new_record = await self.create_record(record_list, InviteFields)
        # Insert the new record into the database
        await self.insert_record(new_record)
        return new_record

    async def update_invite_record(self, record: InviteRecord) -> None:
        """Update an existing Invite record"""
        await self.update_record(record)

    async def delete_invite_record(self, record: InviteRecord) -> None:
        """Delete an existing Invite record"""
        record_id = await record.get_field(InviteFields.record_id)
        await self.delete_record(record_id)

    async def get_invite_records(
        self,
        record_id: str = None,
        team_id: str = None,
        inviter_player_id: str = None,
        invitee_player_id: str = None,
    ) -> list[InviteRecord]:
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
        table = await self.get_table_data()
        existing_records: list[InviteRecord] = []
        for row in table:
            if (
                (
                    not record_id
                    or str(record_id).casefold()
                    == str(row[InviteFields.record_id]).casefold()
                )
                and (
                    not team_id
                    or str(team_id).casefold()
                    == str(row[InviteFields.team_id]).casefold()
                )
                and (
                    not inviter_player_id
                    or inviter_player_id.casefold()
                    == str(row[InviteFields.inviter_player_id]).casefold()
                )
                and (
                    not invitee_player_id
                    or invitee_player_id.casefold()
                    == str(row[InviteFields.invitee_player_id]).casefold()
                )
            ):
                existing_record = InviteRecord(row)
                existing_records.append(existing_record)
        return existing_records
