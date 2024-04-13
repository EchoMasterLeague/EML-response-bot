from database.database import Database
from enum import IntEnum, StrEnum, verify, EnumCheck
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
    team_id = 2  # The id of the team
    player_id = 3  # The id of the player
    is_captain = 4  # Whether or not the player is the captain of the team
    is_co_captain = 5  # Whether or not the player is a co-captain of the team


@verify(EnumCheck.UNIQUE)
class Bool(StrEnum):
    """Lookup for truthy values in the TeamPlayer table"""

    TRUE = "Yes"
    FALSE = "No"


class Record:
    """Record class for this table"""

    def __init__(self, data_list: list[int | float | str | None]):
        """Create a record from a list of data (e.g. from `gsheets`)"""
        self.data_dict = {}
        for field in Field:
            self.data_dict[field.name] = data_list[field.value]

    def to_list(self) -> list[int | float | str | None]:
        """Return the record as a list of data (e.g. for `gsheets`)"""
        data_list = [None] * len(Field)
        for field in Field:
            data_list[field.value] = self.data_dict[field.name]
        return data_list

    def to_dict(self) -> dict:
        """Return the record as a dictionary"""
        return self.data_dict


class Action:
    """A class to manipulate the TeamPlayer table in the database"""

    def __init__(self, db: Database):
        """Initialize the TeamPlayer Action class"""
        self.db: Database = db
        self.worksheet: gspread.worksheet.Worksheet = db.get_db_worksheet(
            constants.LEAGUE_DB_TAB_TEAM_PLAYER
        )

    async def create_team_player(
        self, team_id: str, player_id: str, is_captain: bool, is_co_captain: bool
    ):
        """Create a new TeamPlayer record"""
        existing_record = await self.get_team_player_records(team_id, player_id)
        if existing_record:
            return None
        record_list = [None] * len(Field)
        record_list[Field.record_id] = await helpers.random_id()
        record_list[Field.created_at] = await helpers.iso_timestamp()
        record_list[Field.team_id] = team_id
        record_list[Field.player_id] = player_id
        record_list[Field.is_captain] = (
            Bool.TRUE.value if is_captain else Bool.FALSE.value
        )
        record_list[Field.is_co_captain] = (
            Bool.TRUE.value if is_co_captain else Bool.FALSE.value
        )
        record = Record(record_list)
        try:
            self.worksheet.append_row(record.to_list())
        except gspread.exceptions.APIError as error:
            print(f"Error: {error}")
            return None
        return record.to_dict()

    async def get_team_player_records(self, team_id: str = None, player_id: str = None):
        """Get existing TeamPlayer records"""
        table = self.worksheet.get_all_values()
        existing_records: list[Record] = []
        for row in table:
            if (
                (team_id and team_id.casefold() == str(row[Field.team_id]).casefold())
                or (
                    player_id
                    and player_id.casefold() == str(row[Field.player_id]).casefold()
                )
                or (
                    team_id
                    and player_id
                    and team_id.casefold() == str(row[Field.team_id]).casefold()
                    and player_id.casefold() == str(row[Field.player_id]).casefold()
                )
            ):
                existing_records.append(Record(row))
        return existing_records if existing_records else None

    async def remove_team_player(self, team_id: str, player_id: str):
        """Remove a TeamPlayer record"""
        table = self.worksheet.get_all_values()
        for row in table:
            if row[Field.team_id] == team_id and row[Field.player_id] == player_id:
                self.worksheet.delete_rows(table.index(row) + 1)
                return True
        return False

    # TODO: continue here
