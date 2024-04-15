from database.database import Database
from enum import IntEnum, verify, EnumCheck
from typing import Type
import errors.database_errors as DbErrors
import gspread
import utils.database_helpers as helpers


@verify(EnumCheck.UNIQUE, EnumCheck.CONTINUOUS)
class BaseFields(IntEnum):
    """Lookup for column numbers of fields in this table

    note: `gspread` uses 1-based indexes, these are 0-based.
    These must be the first three fields in ALL tables.
    """

    RECORD_ID = 0  # The unique identifier for the record
    CREATED_AT = 1  # The ISO 8601 timestamp of when the record was created
    UPDATED_AT = 2  # The ISO 8601 timestamp of when the record was last updated


class BaseRecord:
    """Record of a Database Table (row of the worksheet)"""

    def __init__(
        self, fields: Type[BaseFields], data_list: list[int | float | str | None]
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

    async def get_field(self, field: IntEnum) -> int | float | str | None:
        """Get the value of a field"""
        return self._data_dict[field.name]

    async def set_field(self, field: IntEnum, value: int | float | str | None) -> None:
        """Set the value of a field"""
        self._data_dict[field.name] = value

    async def record_fields(self) -> Type[BaseFields]:
        """Get the Enum fields of the record"""
        return self._fields

    async def list_field_names(self) -> list[str]:
        """List the fields of the record"""
        field_list = [None] * len(self._fields)
        for field in self._fields:
            field_list[field.value] = field.name
        return field_list


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
            raise DbErrors.EmlWorksheetRead(
                f"Error reading worksheet: {error.response.text}"
            )
        return table

    async def test_function():
        pass

    async def create_record(
        self, fields: Type[BaseFields], data_list: list[int | float | str | None]
    ):
        """Create a new record"""
        data_list[BaseFields.RECORD_ID] = await helpers.random_id()
        data_list[BaseFields.CREATED_AT] = await helpers.iso_timestamp()
        data_list[BaseFields.UPDATED_AT] = await helpers.iso_timestamp()
        record = self._record_type(fields, data_list)
        return record

    async def insert_record(self, record: BaseRecord):
        """Insert a new record into the table"""
        try:
            self._worksheet.append_row(await record.to_list())
        except gspread.exceptions.APIError as error:
            raise DbErrors.EmlWorksheetWrite(
                f"Error writing to worksheet: {error.response.text}"
            )

    async def get_record(self, record_id: str):
        """Get a record by its ID"""
        table = await self.get_table_data()
        for row in table:
            if row[BaseFields.RECORD_ID] == record_id:
                return self._record_type(row)
        raise DbErrors.EmlRecordNotFound(f"Record '{record_id}' not found")

    async def update_record(self, record: BaseRecord):
        """Update a record in the table"""
        record_id = record.get_field(BaseFields.RECORD_ID)
        record.set_field(BaseFields.UPDATED_AT, await helpers.iso_timestamp())
        table = await self.get_table_data()
        for row in table:
            if row[BaseFields.RECORD_ID] == record_id:
                record_list = await record.to_list()
                self._worksheet.update(f"A{table.index(row) + 1}", [record_list])
                return
        raise DbErrors.EmlRecordNotFound(f"Record '{record_id}' not found")

    async def delete_record(self, record_id: str):
        """Delete a record by its ID"""
        table = await self.get_table_data()
        for row in table:
            if row[BaseFields.RECORD_ID] == record_id:
                try:
                    self._worksheet.delete_rows(table.index(row) + 1)
                except gspread.exceptions.APIError as error:
                    raise DbErrors.EmlWorksheetWrite(
                        f"Error writing to worksheet: {error.response.text}"
                    )
                return
        raise DbErrors.EmlRecordNotFound(f"Record '{record_id}' not found")
