from database.base_table import BaseTable
from database.database_core import CoreDatabase
from database.fields import PlayerFields
from database.records import PlayerRecord, Regions
import constants
import errors.database_errors as DbErrors
import gspread

"""
Player Table
"""


class PlayerTable(BaseTable):
    """A class to manipulate the Player table in the database"""

    _db: CoreDatabase
    _worksheet: gspread.Worksheet

    def __init__(self, db: CoreDatabase):
        """Initialize the Player Table class"""
        super().__init__(db, constants.LEAGUE_DB_TAB_PLAYER, PlayerRecord, PlayerFields)

    async def create_player_record(
        self, discord_id: str, player_name: str, region: str
    ) -> PlayerRecord:
        """Create a new Player record"""
        # Check for existing records to avoid duplication
        existing_records = await self.get_player_records(
            discord_id=discord_id, player_name=player_name
        )
        if existing_records:
            raise DbErrors.EmlRecordAlreadyExists(
                f"Player '{player_name}' already exists"
            )
        # Create the Player record
        record_list = [None] * len(PlayerFields)
        record_list[PlayerFields.discord_id] = discord_id
        record_list[PlayerFields.player_name] = player_name
        record_list[PlayerFields.region] = region
        new_record = await self.create_record(record_list, PlayerFields)
        # Use Discord ID as the record ID
        disrcord_id = await new_record.get_field(PlayerFields.discord_id)
        await new_record.set_field(PlayerFields.record_id, "" + disrcord_id)
        # Insert the new record into the database
        await self.insert_record(new_record)
        return new_record

    async def update_player_record(self, record: PlayerRecord) -> None:
        """Update an existing Player record"""
        await self.update_record(record)

    async def delete_player_record(self, record: PlayerRecord) -> None:
        """Delete an existing Player record"""
        record_id = await record.get_field(PlayerFields.record_id)
        await self.delete_record(record_id)

    async def get_player_records(
        self, record_id: str = None, discord_id: str = None, player_name: str = None
    ) -> list[PlayerRecord]:
        """Get existing Player records"""
        if record_id is None and discord_id is None and player_name is None:
            raise ValueError(
                "At least one of 'record_id', 'discord_id', or 'player_name' is required"
            )
        table = await self.get_table_data()
        existing_records = []
        for row in table:
            if table.index(row) == 0:
                continue
            if (
                (
                    not record_id
                    or str(record_id).casefold()
                    == str(row[PlayerFields.record_id]).casefold()
                )
                and (
                    not discord_id
                    or str(discord_id).casefold()
                    == str(row[PlayerFields.discord_id]).casefold()
                )
                and (
                    not player_name
                    or player_name.casefold()
                    == str(row[PlayerFields.player_name]).casefold()
                )
            ):
                existing_records.append(PlayerRecord(row))
        return existing_records

    async def get_players_by_region(self, region: str) -> list[PlayerRecord]:
        """Get all players from a specific region"""
        # Validate the region
        is_region_allowed = False
        allowed_region_list = [r.value for r in Regions]
        for allowed_region in allowed_region_list:
            if region.casefold() == allowed_region.casefold():
                region = allowed_region
                is_region_allowed = True
                break
        if not is_region_allowed:
            raise DbErrors.EmlRegionNotFound(
                f"Region '{region}' not available. Available Regions: {allowed_region_list}"
            )
        # Get the players from the region
        table = await self.get_table_data()
        players = []
        for row in table:
            if table.index(row) == 0:
                continue
            if region == row[PlayerFields.region]:
                player = PlayerRecord(row)
                players.append(player)
        return players
