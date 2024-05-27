from database.base_table import BaseTable
from database.database_core import CoreDatabase
from database.fields import CooldownFields
from database.records import CooldownRecord
import constants
import gspread
import utils.general_helpers as general_helpers

"""
Cooldown Table
"""


class CooldownTable(BaseTable):
    """A class to manipulate the Cooldown table in the database"""

    _db: CoreDatabase
    _worksheet: gspread.Worksheet

    def __init__(self, db: CoreDatabase):
        """Initialize the Cooldown Table class"""
        super().__init__(
            db, constants.LEAGUE_DB_TAB_COOLDOWN, CooldownRecord, CooldownFields
        )

    async def create_cooldown_record(
        self,
        player_id: str,
        old_team_id: str,
        player_name: str,
        old_team_name: str,
        expiration: int = None,
    ) -> CooldownRecord:
        """Create a new Cooldown record, or update an existing one"""
        # prepare info for new (or existing) record
        expiration_epoch = await general_helpers.upcoming_monday()
        expiration = expiration if expiration else expiration_epoch
        expires_at = await general_helpers.iso_timestamp(expiration)
        # Check for existing records to avoid duplication
        existing_records = await self.get_cooldown_records(player_id=player_id)
        existing_record: CooldownRecord
        existing_record = existing_records[0] if existing_records else None
        if existing_record:
            # Update existing record in the database
            await existing_record.set_field(CooldownFields.expires_at, expires_at)
            await existing_record.set_field(CooldownFields.old_team_id, old_team_id)
            await existing_record.set_field(CooldownFields.vw_player, player_name)
            await existing_record.set_field(CooldownFields.vw_old_team, old_team_name)
            await self.update_cooldown_record(existing_record)
            return existing_record
        # Create the new record
        record_list = [None] * len(CooldownFields)
        record_list[CooldownFields.player_id] = player_id
        record_list[CooldownFields.old_team_id] = old_team_id
        record_list[CooldownFields.expires_at] = expires_at
        record_list[CooldownFields.vw_player] = player_name
        record_list[CooldownFields.vw_old_team] = old_team_name
        new_record = await self.create_record(record_list, CooldownFields)
        # Insert the new record into the database
        await self.insert_record(new_record)
        return new_record

    async def update_cooldown_record(self, record: CooldownRecord) -> None:
        """Update an existing Cooldown record"""
        await self.update_record(record)

    async def delete_cooldown_record(self, record: CooldownRecord) -> None:
        """Delete an existing Cooldown record"""
        record_id = await record.get_field(CooldownFields.record_id)
        await self.delete_record(record_id)

    async def get_cooldown_records(
        self,
        record_id: str = None,
        player_id: str = None,
        expires_before: int = None,
        expires_after: int = None,
    ) -> list[CooldownRecord]:
        """Get an existing Cooldown record

        Note: Since this has to walk the whole table anyway, this is also used to clean up expired records
        """
        if (
            record_id is None
            and player_id is None
            and expires_before is None
            and expires_after is None
        ):
            raise ValueError(
                "At least one of 'record_id', 'player_id', 'expires_before', or 'expires_after' is required"
            )
        now = await general_helpers.epoch_timestamp()
        table = await self.get_table_data()
        existing_records: list[CooldownRecord] = []
        expired_records: list[CooldownRecord] = []
        for row in table:
            # Skip header row
            if table.index(row) == 0:
                continue
            # Check for expired records
            expiration_epoch = int(
                await general_helpers.epoch_timestamp(row[CooldownFields.expires_at])
            )
            if int(now) > expiration_epoch:
                expired_record = CooldownRecord(row)
                expired_records.append(expired_record)
                continue
            # Check for matching records
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
                and (not expires_before or int(expires_before) > int(expiration_epoch))
                and (not expires_after or int(expires_after) < int(expiration_epoch))
            ):
                # Add the matching record to the list
                existing_record = CooldownRecord(row)
                existing_records.append(existing_record)
        # Remove expired records from the database
        for record in expired_records:
            await self.delete_cooldown_record(record)
        # Return the matched records
        return existing_records
