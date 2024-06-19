from database.base_table import BaseTable
from database.database_core import CoreDatabase
from database.enums import Bool
from database.fields import CommandLockFields
from database.records import CommandLockRecord
import constants
import gspread
import logging

logger = logging.getLogger(__name__)

"""
CommandLock Table
"""


class CommandLockTable(BaseTable):
    """A class to manipulate the CommandLock table in the database"""

    _db: CoreDatabase
    _worksheet: gspread.Worksheet

    def __init__(self, db: CoreDatabase):
        """Initialize the CommandLock Table class"""
        super().__init__(
            db,
            constants.LEAGUE_DB_TAB_COMMAND_LOCK,
            CommandLockRecord,
            CommandLockFields,
        )

    async def create_command_lock_record(
        self, command_name: str, is_allowed: bool
    ) -> CommandLockRecord:
        """Create a new CommandLock record, or update an existing one"""
        # Check for existing records to avoid duplication
        existing_records = await self.get_command_lock_records(
            command_name == command_name
        )
        existing_record = existing_records[0] if existing_records else None
        if existing_record:
            # Update existing record in the database
            existing_record.set_field(CommandLockFields.is_allowed, is_allowed)
            await self.update_command_lock_record(existing_record)
            return existing_record
        # Create the new record
        record_list = [None] * len(CommandLockFields)
        record_list[CommandLockFields.command_name] = command_name
        record_list[CommandLockFields.is_allowed] = is_allowed
        new_record = await self.create_record(record_list, CommandLockFields)
        # Insert the new record into the database
        await self.insert_record(new_record)
        return new_record

    async def update_command_lock_record(self, record: CommandLockRecord) -> None:
        """Update an existing CommandLock record"""
        await self.update_record(record)

    async def delete_command_lock_record(self, record: CommandLockRecord) -> None:
        """Delete an existing CommandLock record"""
        record_id = await record.get_field(CommandLockFields.record_id)
        await self.delete_record(record_id)

    async def get_command_lock_records(
        self, record_id: str = None, command_name: str = None, is_allowed: bool = None
    ) -> list[CommandLockRecord]:
        """Get an existing CommandLock record"""
        # Parameter conversion
        if is_allowed is not None:
            is_allowed = Bool.TRUE if is_allowed else Bool.FALSE
        # Walk the table
        table = await self.get_table_data()
        existing_records = []
        for row in table[1:]:  # skip header row
            # Check for matched record
            if (
                (
                    not record_id
                    or str(record_id).casefold()
                    == str(row[CommandLockFields.record_id]).casefold()
                )
                and (
                    not command_name
                    or str(command_name).casefold()
                    == str(row[CommandLockFields.command_name]).casefold()
                )
                and (
                    not is_allowed
                    or str(is_allowed).casefold()
                    == str(row[CommandLockFields.is_allowed]).casefold()
                )
            ):
                # Add matched record
                existing_record = CommandLockRecord(row)
                existing_records.append(existing_record)
        # Return matched records
        return existing_records
