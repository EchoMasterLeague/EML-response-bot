from database.database import Database
from enum import IntEnum, verify, EnumCheck
from typing import Type
import errors.database_errors as DbErrors
import gspread
import utils.database_helpers as helpers

"""
Base Table

This module contains the base classes for all database tables.
All other tables must inherit from these classes.

## Generally ##

- `*Fields` classes: contain the column numbers of the fields in the table.
- `*Record` classes: represent records of a database table (rows of the worksheet).
- `*Table`  classes: interact with a table in the database.

## Specifically ##

- `BaseFields` class: contains the mandatory first three fields of all tables
    - record_id: The unique identifier for the record
    - created_at: The ISO 8601 timestamp of when the record was created
    - updated_at: The ISO 8601 timestamp of when the record was last updated

- `BaseRecord` class: contains the following methods available to all tables
    - `to_list()`: Return the record as a list of data (e.g. for `gsheets`)
    - `to_dict()`: Return the record as a dictionary
    - `get_field(field_enum)`: Get the value of a field
    - `set_field(field_enum, value)`: Set the value of a field

- `BaseTable` class: provides the common "CRUD" operations for all tables
    - `get_table_data()`: Get all the data from the worksheet. (i.e. the table)
    ### Create
    - `create_record(data_list)`: Create a new record
    - `insert_record(record)`: Insert a new record into the table
    ### Read
    - `get_record(record_id)`: Get a record by its ID
    ### Update
    - `update_record(record)`: Update a record in the table
    ### Delete
    - `delete_record(record_id)`: Delete a record by its ID
"""


@verify(EnumCheck.UNIQUE, EnumCheck.CONTINUOUS)
class BaseFields(IntEnum):
    """Lookup for column numbers of fields in this table

    note: `gspread` uses 1-based indexes, these are 0-based.
    These must be the first three fields in ALL tables.
    """

    record_id = 0  # The unique identifier for the record
    created_at = 1  # The ISO 8601 timestamp of when the record was created
    updated_at = 2  # The ISO 8601 timestamp of when the record was last updated


class BaseRecord:
    """Record of a Database Table (row of the worksheet)"""

    def __init__(
        self,
        data_list: list[int | float | str | None],
        fields: Type[BaseFields] = BaseFields,
    ):
        """Create a record from a list of data (e.g. from `gsheets`)"""
        self._fields = fields
        self._data_dict = {}
        for field in self._fields:
            self._data_dict[field.name] = data_list[field.value]

    async def to_list(self) -> list[int | float | str | None]:
        """Return the record as a list of data (e.g. for `gsheets`)"""
        data_list = [None] * len(self._fields)
        for field in self._fields:
            data_list[field.value] = self._data_dict[field.name]
        return data_list

    async def to_dict(self) -> dict:
        """Return the record as a dictionary"""
        return self._data_dict

    async def get_field(self, field_enum: int) -> int | float | str | None:
        """Get the value of a field"""
        for field in self._fields:
            if field.value == field_enum:
                return self._data_dict[field.name]
        raise ValueError(f"Field '{field_enum}' not found in '{self._fields}'")

    async def set_field(self, field_enum: int, value: int | float | str | None) -> None:
        """Set the value of a field"""
        for field in self._fields:
            if field.value == field_enum:
                self._data_dict[field.name] = value
                return
        raise ValueError(f"Field '{field_enum}' not found in '{self._fields}'")


class BaseTable:
    def __init__(self, db: Database, tab_name: str, record_type: Type[BaseRecord]):
        self._db: Database = db
        self._record_type: Type[BaseRecord] = record_type
        try:
            self._worksheet: gspread.worksheet.Worksheet = db.get_db_worksheet(tab_name)
        except gspread.exceptions.WorksheetNotFound as error:
            raise DbErrors.EmlWorksheetDoesNotExist(
                f"Worksheet '{tab_name}' does not exist: {error}"
            )

    async def get_table_data(self):
        """Get all the data from the workseet"""
        try:
            table = self._worksheet.get_all_values()
        except gspread.exceptions.APIError as error:
            raise DbErrors.EmlWorksheetReadError(
                f"Error reading worksheet: {error.response.text}"
            )
        return table

    async def create_record(
        self,
        data_list: list[int | float | str | None],
        fields: Type[BaseFields] = BaseFields,
    ):
        """Create a new record"""
        data_list[BaseFields.record_id] = await helpers.random_id()
        data_list[BaseFields.created_at] = await helpers.iso_timestamp()
        data_list[BaseFields.updated_at] = await helpers.iso_timestamp()
        record = self._record_type(data_list=data_list, fields=fields)
        return record

    async def insert_record(self, record: BaseRecord):
        """Insert a new record into the table"""
        try:
            self._worksheet.append_row(await record.to_list())
        except gspread.exceptions.APIError as error:
            raise DbErrors.EmlWorksheetWriteError(
                f"Error writing to worksheet: {error.response.text}"
            )

    async def get_record(self, record_id: str):
        """Get a record by its ID"""
        table = await self.get_table_data()
        for row in table:
            if row[BaseFields.record_id] == record_id:
                return self._record_type(row)
        raise DbErrors.EmlRecordNotFound(f"Record '{record_id}' not found")

    async def update_record(self, record: BaseRecord):
        """Update a record in the table"""
        record_id = await record.get_field(BaseFields.record_id)
        await record.set_field(BaseFields.updated_at, await helpers.iso_timestamp())
        table = await self.get_table_data()
        for row in table:
            if row[BaseFields.record_id] == record_id:
                record_list = await record.to_list()
                self._worksheet.update(f"A{table.index(row) + 1}", [record_list])
                return
        raise DbErrors.EmlRecordNotFound(f"Record '{record_id}' not found")

    async def delete_record(self, record_id: str):
        """Delete a record by its ID"""
        table = await self.get_table_data()
        for row in table:
            if row[BaseFields.record_id] == record_id:
                try:
                    self._worksheet.delete_rows(table.index(row) + 1)
                except gspread.exceptions.APIError as error:
                    raise DbErrors.EmlWorksheetWriteError(
                        f"Error writing to worksheet: {error.response.text}"
                    )
                return
        raise DbErrors.EmlRecordNotFound(f"Record '{record_id}' not found")
