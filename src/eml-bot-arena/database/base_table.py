from database.database_core import CoreDatabase
from database.fields import BaseFields
from database.records import BaseRecord
from enum import IntEnum, StrEnum, verify, EnumCheck
from typing import Type
import constants
import errors.database_errors as DbErrors
import gspread
import utils.general_helpers as general_helpers
import logging

logger = logging.getLogger(__name__)

"""
Base Table
"""


class BaseTable:
    """A class to manipulate a table in the database

    Provides the common "CRUD" operations for all tables
    ## Create:
    - `create_record(data_list)`: Create a new record
    - `insert_record(record)`: Insert a new record into the table
    ## Read:
    - `get_table_data()`: Get all the data from the worksheet. (i.e. the table)
    - `get_record(record_id)`: Get a record by its ID
    ## Update:
    - `update_record(record)`: Update a record in the table
    ## Delete:
    - `delete_record(record_id)`: Delete a record by its ID
    """

    def __init__(
        self,
        db: CoreDatabase,
        table_name: str,
        record_type: Type[BaseRecord],
        fields: Type[BaseFields],
    ):
        self.table_name: str = table_name
        self._db: CoreDatabase = db
        self._record_type: Type[BaseRecord] = record_type
        self._fields: Type[BaseFields] = fields
        self._history_table: HistoryTable
        try:
            table_worksheet: gspread.worksheet.Worksheet
            table_worksheet = db.get_table_worksheet(table_name)
        except DbErrors.EmlWorksheetDoesNotExist as error:
            # Create the worksheet if it doesn't exist
            table_worksheet = db.create_table_worksheet(table_name)
            # Add the fields to the worksheet
            field_list = [field.name for field in fields]
            table_worksheet.update(f"A1", [field_list])
        except DbErrors.EmlWorksheetCreateError as error:
            message = f"Worksheet '{table_name}' does not exist and could not be created: {error}"
            raise DbErrors.EmlWorksheetDoesNotExist(message)
        history_table_name = f"{table_name}{constants.LEAGUE_DB_TAB_SUFFIX_HISTORY}"
        self._history_table = HistoryTable(db, history_table_name, record_type, fields)

    async def get_table_data(self):
        """Get all the data from the workseet"""
        try:
            table = await self._db.get_table_data(self.table_name)
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
        data_list[BaseFields.record_id] = await general_helpers.random_id()
        data_list[BaseFields.created_at] = await general_helpers.iso_timestamp()
        data_list[BaseFields.updated_at] = await general_helpers.iso_timestamp()
        record = self._record_type(data_list=data_list, fields=fields)
        return record

    async def insert_record(self, record: BaseRecord):
        """Insert a new record into the table"""
        try:
            # Update History
            operation = HistoryOperations.CREATE
            await self._history_table.create_history_record(record, operation)
            # Insert Record
            record_list = await record.to_list()
            await self._db.append_row(table_name=self.table_name, row_data=record_list)
        except gspread.exceptions.APIError as error:
            raise DbErrors.EmlWorksheetWriteError(
                f"Error writing to worksheet: {error.response.text}"
            )

    async def update_record(self, record: BaseRecord):
        """Update a record in the table"""
        record_id = await record.get_field(BaseFields.record_id)
        await record.set_field(
            BaseFields.updated_at, await general_helpers.iso_timestamp()
        )
        table = await self.get_table_data()
        for row in table:
            if table.index(row) == 0:
                continue
            if row[BaseFields.record_id] == record_id:
                # Update History
                operation = HistoryOperations.UPDATE
                await self._history_table.create_history_record(record, operation)
                # Update Records
                record_list = await record.to_list()
                await self._db.update_row(
                    table_name=self.table_name, row_data=record_list
                )
                return
        raise DbErrors.EmlRecordNotFound(f"Record '{record_id}' not found")

    async def delete_record(self, record_id: str):
        """Delete a record from the table"""
        table = await self.get_table_data()
        for row in table:
            if table.index(row) == 0:
                continue
            if row[BaseFields.record_id] == record_id:
                try:
                    # Update History
                    record = self._record_type(row)
                    operation = HistoryOperations.DELETE
                    await self._history_table.create_history_record(record, operation)
                    # Delete Record
                    await self._db.delete_row(
                        table_name=self.table_name, record_id=record_id
                    )
                except gspread.exceptions.APIError as error:
                    raise DbErrors.EmlWorksheetWriteError(
                        f"Error writing to worksheet: {error.response.text}"
                    )
                return
        raise DbErrors.EmlRecordNotFound(f"Record '{record_id}' not found")


"""
Base History Table
"""


@verify(EnumCheck.UNIQUE, EnumCheck.CONTINUOUS)
class HistoryFields(IntEnum):
    """Lookup for column numbers of fields in this table

    note: `gspread` uses 1-based indexes, these are 0-based.
    """

    history_id = 0  # The unique identifier for the history record
    history_created_at = (
        1  # The ISO 8601 timestamp of when the history record was created
    )
    history_operation = 2  # The operation performed on the original record


@verify(EnumCheck.UNIQUE)
class HistoryOperations(StrEnum):
    """Lookup for Operation values in the History table"""

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class HistoryTable:
    """A class to manipulate a History table in the database"""

    def __init__(
        self,
        db: CoreDatabase,
        table_name: str,
        record_type: Type[BaseRecord] = BaseRecord,
        fields: Type[BaseFields] = BaseFields,
    ):
        self.table_name: str = table_name
        self._db: CoreDatabase = db
        self._record_type: Type[BaseRecord] = record_type
        self._record_fields: Type[BaseFields] = fields
        try:
            history_worksheet: gspread.worksheet.Worksheet
            history_worksheet = db.get_table_worksheet(table_name)
        except DbErrors.EmlWorksheetDoesNotExist as error:
            # Create the worksheet if it doesn't exist
            history_worksheet = db.create_table_worksheet(table_name)
            # Add the fields to the worksheet
            fields: Type[IntEnum] = self._record_fields
            original_field_list = [field.name for field in fields]
            history_field_list = [field.name for field in HistoryFields]
            field_list = history_field_list + original_field_list
            history_worksheet.update(f"A1", [field_list])
        except DbErrors.EmlWorksheetCreateError as error:
            message = f"Worksheet '{table_name}' does not exist and could not be created: {error}"
            raise DbErrors.EmlWorksheetDoesNotExist(message)

    async def create_history_record(
        self, record: BaseRecord, operation: HistoryOperations
    ) -> None:
        """Create a new history record for the given record"""
        # Get the original record as a list
        original_list = await record.to_list()
        # Create the history record list
        history_list = [None] * len(HistoryFields) + original_list
        history_list[HistoryFields.history_id] = await general_helpers.random_id()
        history_list[HistoryFields.history_created_at] = (
            await general_helpers.iso_timestamp()
        )
        history_list[HistoryFields.history_operation] = operation.value
        # insert the history record list into the table
        try:
            await self._db.append_row(table_name=self.table_name, row_data=history_list)
        except gspread.exceptions.APIError as error:
            raise DbErrors.EmlWorksheetWriteError(
                f"Error writing to worksheet: {error.response.text}"
            )
