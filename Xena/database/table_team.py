from database.database import Database
from enum import IntEnum, StrEnum, verify, EnumCheck
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
    team_name = 2  # The name of the team
    status = 3  # The status of the team (e.g. "Active", "Inactive")


@verify(EnumCheck.UNIQUE)
class Status(StrEnum):
    """Lookup for status values in the Team table"""

    ACTIVE = "Active"  # The team is active
    INACTIVE = "Inactive"  # The team is inactive


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
    """A class to manipulate the Team table in the database"""

    def __init__(self, db: Database):
        """Initialize the Team Action class"""
        self.db: Database = db
        self.worksheet: gspread.worksheet.Worksheet = db.get_db_worksheet(
            constants.LEAGUE_DB_TAB_TEAM
        )

    async def create_team(self, team_name: str):
        """Create a new Team record"""
        existing_record = await self.get_team(team_name)
        if existing_record:
            return None
        record_list = [None] * len(Field)
        record_list[Field.record_id] = await helpers.random_id()
        record_list[Field.created_at] = await helpers.iso_timestamp()
        record_list[Field.team_name] = team_name
        record_list[Field.status] = Status.ACTIVE
        record = Record(record_list)
        try:
            self.worksheet.append_row(record.to_list())
        except gspread.exceptions.APIError as error:
            print(f"Error: {error}")
            return None
        return record

    async def get_team(self, team_name: str):
        """Get an existing Team record"""
        cell_list = self.worksheet.findall(
            query=team_name,
            in_column=Field.team_name + 1,  # `gspread` uses 1-based indexes
            case_sensitive=False,
        )
        for cell in cell_list:
            row = self.worksheet.row_values(cell.row)
            record = Record(row)
            return record
        return None
