from database.database import Database
from enum import IntEnum, verify, EnumCheck
from typing import List
import constants
import database.helpers as helpers
import gspread


@verify(EnumCheck.UNIQUE, EnumCheck.CONTINUOUS)
class Field(IntEnum):
    """Lookup for column numbers of fields in this table

    note: `gspread` uses 1-based indexes, these are 0-based.
    """

    record_id = 0  # The unique identifier for the record
    created_at = 1  # The ISO 8601 timestamp of when the record was created
    discord_id = 2  # Numeric Discord ID of the player
    player_name = 3  # Display Name of the player


class Record:
    """Record class for this table"""

    def __init__(self, data_list: List[int | float | str | None]):
        """Create a record from a list of data (e.g. from `gsheets`)"""
        self.data_dict = {}
        for field in Field:
            self.data_dict[field.name] = data_list[field.value]

    def to_list(self) -> List[int | float | str | None]:
        """Return the record as a list of data (e.g. for `gsheets`)"""
        data_list = [None] * len(Field)
        for field in Field:
            data_list[field.value] = self.data_dict[field.name]
        return data_list

    def to_dict(self) -> dict:
        """Return the record as a dictionary"""
        return self.data_dict


class Action:
    """A class to manipulate the Player table in the database"""

    def __init__(self, db: Database):
        """Initialize the Player Action class"""
        self.db: Database = db
        self.worksheet: gspread.worksheet.Worksheet = db.get_db_worksheet(
            constants.LEAGUE_DB_TAB_PLAYER
        )

    async def create_player(self, discord_id: str, player_name: str):
        """Create a new Player record"""
        existing_record = await self.get_player(discord_id, player_name)
        if existing_record:
            return None
        record_list = [None] * len(Field)
        record_list[Field.record_id] = await helpers.random_id()
        record_list[Field.created_at] = await helpers.iso_timestamp()
        record_list[Field.discord_id] = discord_id
        record_list[Field.player_name] = player_name
        new_record = Record(record_list)
        try:
            self.worksheet.append_row(new_record.to_list())
        except gspread.exceptions.APIError as error:
            print(f"Error: {error}")
            return None
        return new_record

    async def get_player(self, discord_id: str = None, player_name: str = None):
        """Get an existing Player record"""
        table = self.worksheet.get_all_values()
        for row in table:
            if (
                discord_id.casefold() == str(row[Field.discord_id]).casefold()
                or player_name.casefold() == str(row[Field.player_name]).casefold()
            ):
                existing_record = Record(row)
                return existing_record
        return None
