from database.base_table import BaseFields, BaseRecord, BaseTable
from database.database import Database
from enum import IntEnum, verify, EnumCheck
from typing import Type
import constants
import errors.database_errors as DbErrors
import gspread


@verify(EnumCheck.UNIQUE, EnumCheck.CONTINUOUS)
class ExampleFields(IntEnum):
    """Lookup for column numbers of fields in this table

    note: `gspread` uses 1-based indexes, these are 0-based.
    """

    RECORD_ID = BaseFields.RECORD_ID
    CREATED_AT = BaseFields.CREATED_AT
    UPDATED_AT = BaseFields.UPDATED_AT
    EAXMPLE_A = 2  # EXAMPLE_A description
    EXAMPLE_B = 3  # EXAMPLE_B description


class ExampleRecord(BaseRecord):
    """Record class for this table"""

    _fields: Type[ExampleFields]
    _data_dict: dict

    def __init__(self, data_list: list[int | float | str | None]):
        """Create a record from a list of data (e.g. from `gsheets`)"""
        super().__init__(ExampleFields, data_list)


class ExmapleTable(BaseTable):
    """A class to manipulate the Example table in the database"""

    _db: Database
    _worksheet: gspread.Worksheet

    def __init__(self, db: Database):
        """Initialize the Example Action class"""
        super().__init__(db, constants.LEAGUE_DB_TAB_EXAMPLE, ExampleRecord)

    async def create_example(self, example_a: str, example_b: str) -> ExampleRecord:
        """Create a new Example record"""
        # Check for existing records to avoid duplication
        existing_record = await self.get_example(
            example_a=example_a, example_b=example_b
        )
        if existing_record:
            raise DbErrors.EmlRecordAlreadyExists(
                f"Example record already exists: {existing_record.to_dict()}"
            )
        # Create the Example record
        record_list = [None] * len(ExampleFields)
        record_list[ExampleFields.EAXMPLE_A] = example_a
        record_list[ExampleFields.EXAMPLE_B] = example_b
        new_record = super().create_record(ExampleRecord, record_list)
        # Insert the new record into the "database"
        await super().insert_record(new_record)
        return new_record

    async def update_record(self, record: BaseRecord):
        """Update an existing Example record"""
        return await super().update_record(record)

    async def delete_record(self, record: BaseRecord):
        """Delete an existing Example record"""
        record_id = record.to_dict()[ExampleFields.RECORD_ID]
        return await super().delete_record(record_id)

    async def get_example(
        self, record_id: str = None, example_a: str = None, example_b: str = None
    ) -> ExampleRecord:
        """Get an existing Example record"""
        if record_id is None and example_a is None and example_b is None:
            raise DbErrors.EmlRecordNotFound(
                "At least one of 'record_id', 'example_a', or 'example_b' must be provided"
            )
        table = self.get_table_data()
        for row in table:
            if (
                (
                    not record_id
                    or str(record_id).casefold()
                    == str(row[ExampleFields.RECORD_ID]).casefold()
                )
                and (
                    not example_a
                    or str(example_a).casefold()
                    == str(row[ExampleFields.EXAMPLE_A]).casefold()
                )
                and (
                    not example_b
                    or str(example_b).casefold()
                    == str(row[ExampleFields.EXAMPLE_B]).casefold()
                )
            ):
                existing_record = ExampleRecord(row)
                return existing_record
        raise DbErrors.EmlRecordNotFound("Example not found")
