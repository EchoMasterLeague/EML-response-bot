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
    example_a = 2  # example_a description
    example_b = 3  # example_b description


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
    """A class to manipulate the Example table in the database"""

    def __init__(self, db: Database):
        """Initialize the Example Action class"""
        self.db: Database = db
        self.worksheet: gspread.worksheet.Worksheet = db.get_db_worksheet(
            constants.LEAGUE_DB_TAB_EXAMPLE
        )

    async def create_example(self, example_a: str, example_b: str):
        """Create a new Example record"""
        existing_record = await self.get_example(
            example_a=example_a, example_b=example_b
        )
        if existing_record:
            return None
        record_list = [None] * len(Field)
        record_list[Field.record_id] = await helpers.random_id()
        record_list[Field.created_at] = await helpers.iso_timestamp()
        record_list[Field.example_a] = example_a
        record_list[Field.example_b] = example_b
        record = Record(record_list)
        try:
            self.worksheet.append_row(record.to_list())
        except gspread.exceptions.APIError as error:
            print(f"Error: {error}")
            return None
        return record.to_dict()

    async def get_example_few_calls_version(self, example_a: str, example_b: str):
        """Get an existing Example record

        This version uses more bandwidth but fewer API calls.
        Use this version for small tables.
        """
        table = self.worksheet.get_all_values()
        for row in table:
            if row[Field.example_a] == example_a and row[Field.example_b] == example_b:
                existing_record = Record(row)
                return existing_record
        return None

    async def get_example_low_data_version(self, example_a: str, example_b: str):
        """Get an existing Example record

        This version uses less bandwidth but more API calls.
        Use this version for large tables.
        """
        cell_list: List[gspread.cell.Cell] = []
        if example_a:
            cell_list += self.worksheet.findall(
                query=example_a,
                in_column=Field.example_a + 1,  # `gspread` uses 1-based indexes
                case_sensitive=False,
            )
        if example_b:
            cell_list += self.worksheet.findall(
                query=example_b,
                in_column=Field.example_b + 1,  # `gspread` uses 1-based indexes
                case_sensitive=False,
            )
        for cell in cell_list:
            row = self.worksheet.row_values(cell.row)
            record = Record(row)
            return record.to_dict()
        return None
