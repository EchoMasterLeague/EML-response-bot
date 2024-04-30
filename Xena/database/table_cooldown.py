from database.base_table import BaseFields, BaseRecord, BaseTable
from database.database import Database
from enum import IntEnum, verify, EnumCheck, StrEnum
from typing import Type
import constants
import errors.database_errors as DbErrors
import gspread
import utils.database_helpers as helpers

"""
Player Table
"""


@verify(EnumCheck.UNIQUE, EnumCheck.CONTINUOUS)
class CooldownFields(IntEnum):
    """Lookup for column numbers of fields in this table

    note: `gspread` uses 1-based indexes, these are 0-based.
    """

    record_id = BaseFields.record_id
    created_at = BaseFields.created_at
    updated_at = BaseFields.updated_at
    player_id = 3  # Record ID of the player
    expires_at = 4  # Timestamp when the cooldown expires


class CooldownRecord(BaseRecord):
    """Record class for this table"""

    fields: Type[CooldownFields]
    _data_dict: dict

    def __init__(
        self,
        data_list: list[int | float | str | None],
        fields: Type[CooldownFields] = CooldownFields,
    ):
        """Create a record from a list of data (e.g. from `gsheets`)"""
        super().__init__(data_list, fields)


class CooldownTable(BaseTable):
    """A class to manipulate the Cooldown table in the database"""

    _db: Database
    _worksheet: gspread.Worksheet

    def __init__(self, db: Database):
        """Initialize the Cooldown Action class"""
        super().__init__(
            db, constants.LEAGUE_DB_TAB_COOLDOWN, CooldownRecord, CooldownFields
        )

    async def create_cooldown_record(
        self, player_id: str, expiration: int
    ) -> CooldownRecord:
        """Create a new Cooldown record, or update an existing one"""
        # Check for existing records to avoid duplication
        existing_record = await self.get_cooldown_record(player_id=player_id)
        if existing_record:
            existing_record.set_field(CooldownFields.expires_at, expiration)
            await self.update_cooldown_record(existing_record)
            return existing_record
        # Create the new record
        record_list = [None] * len(CooldownFields)
        record_list[CooldownFields.player_id] = player_id
        record_list[CooldownFields.expires_at] = expiration
        new_record = await self.create_record(record_list, CooldownFields)
        # Insert the new record into the database
        await self.insert_record(new_record)
        return new_record

    async def update_cooldown_record(self, record: CooldownRecord) -> None:
        """Update an existing Player record"""
        await self.update_record(record)

    async def delete_cooldown_record(self, record: CooldownRecord) -> None:
        """Delete an existing Player record"""
        record_id = await record.get_field(CooldownFields.record_id)
        await self.delete_record(record_id)

    async def get_cooldown_record(
        self,
        record_id: str = None,
        player_id: str = None,
        expires_before: int = None,
        expires_after: int = None,
    ) -> CooldownRecord:
        """Get an existing Cooldown record"""
        if (
            record_id is None
            and player_id is None
            and expires_before is None
            and expires_after is None
        ):
            raise ValueError(
                "At least one of 'record_id', 'player_id', 'expires_before', or 'expires_after' is required"
            )
        table = await self.get_table_data()
        for row in table:
            if (
                (
                    not record_id
                    or str(record_id).casefold()
                    == str(row[CooldownFields.record_id]).casefold()
                )
                and (
                    not player_id
                    or str(player_id).casefold()
                    == str(row[CooldownFields.player_id]).casefold()
                )
                and (
                    not expires_before
                    or expires_before
                    > await helpers.epoch_timestamp(row[CooldownFields.expires_at])
                )
                and (
                    not expires_after
                    or expires_after
                    < await helpers.epoch_timestamp(row[CooldownFields.expires_at])
                )
            ):
                existing_record = CooldownRecord(row)
                return existing_record
        return None
