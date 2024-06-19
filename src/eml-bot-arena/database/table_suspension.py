from database.base_table import BaseTable
from database.database_core import CoreDatabase
from database.fields import SuspensionFields
from database.records import SuspensionRecord
import constants
import gspread
import utils.general_helpers as general_helpers
import logging

logger = logging.getLogger(__name__)

"""
Suspension Table
"""


class SuspensionTable(BaseTable):
    """A class to manipulate the Suspension table in the database"""

    _db: CoreDatabase
    _worksheet: gspread.Worksheet

    def __init__(self, db: CoreDatabase):
        """Initialize the Suspension Table class"""
        super().__init__(
            db, constants.LEAGUE_DB_TAB_SUSPENSION, SuspensionRecord, SuspensionFields
        )

    async def create_suspension_record(
        self,
        player_id: str,
        player_name: str,
        reason: str,
        expiration: int,
    ) -> SuspensionRecord:
        """Create a new Suspension record, or update an existing one"""
        # prepare info for new (or existing) record
        now = await general_helpers.epoch_timestamp()
        expiration_seconds = expiration * 60 * 60 * 24 if expiration else 0
        expiration_epoch = now + expiration_seconds
        expires_at = await general_helpers.iso_timestamp(expiration_epoch)
        # Check for existing records to avoid duplication
        existing_records = await self.get_suspension_records(player_id=player_id)
        existing_record: SuspensionRecord
        existing_record = existing_records[0] if existing_records else None
        if existing_record:
            # Update existing record in the database
            await existing_record.set_field(SuspensionFields.expires_at, expires_at)
            await existing_record.set_field(SuspensionFields.reason, reason)
            await existing_record.set_field(SuspensionFields.vw_player, player_name)
            await self.update_suspension_record(existing_record)
            return existing_record
        # Create the new record
        record_list = [None] * len(SuspensionFields)
        record_list[SuspensionFields.player_id] = player_id
        record_list[SuspensionFields.expires_at] = expires_at
        record_list[SuspensionFields.reason] = reason
        record_list[SuspensionFields.vw_player] = player_name
        new_record = await self.create_record(record_list, SuspensionFields)
        # Insert the new record into the database
        await self.insert_record(new_record)
        return new_record

    async def update_suspension_record(self, record: SuspensionRecord) -> None:
        """Update an existing Suspension record"""
        await self.update_record(record)

    async def delete_suspension_record(self, record: SuspensionRecord) -> None:
        """Delete an existing Suspension record"""
        record_id = await record.get_field(SuspensionFields.record_id)
        await self.delete_record(record_id)

    async def get_suspension_records(
        self,
        record_id: str = None,
        player_id: str = None,
        expires_before: int = None,
        expires_after: int = None,
    ) -> list[SuspensionRecord]:
        """Get an existing Suspension record

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
                row[SuspensionFields.expires_at]
            )
            if now > expiration_epoch:
                expired_record = SuspensionRecord(row)
                expired_records.append(expired_record)
                continue
            # Check for matched records
            if (
                (
                    not record_id
                    or str(record_id).casefold()
                    == str(row[SuspensionFields.record_id]).casefold()
                )
                and (
                    not player_id
                    or str(player_id).casefold()
                    == str(row[SuspensionFields.player_id]).casefold()
                )
                and (not expires_before or int(expires_before) > int(expiration_epoch))
                and (not expires_after or int(expires_after) < int(expiration_epoch))
            ):
                # Add the matching record to the list
                existing_record = SuspensionRecord(row)
                existing_records.append(existing_record)
        # Remove expired records from the database
        for record in expired_records:
            await self.delete_suspension_record(record)
        # Return the matched records
        return existing_records
