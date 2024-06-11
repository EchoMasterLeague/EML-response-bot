from database.base_table import BaseTable
from database.database_core import CoreDatabase
from database.fields import ExampleFields
from database.records import ExampleRecord
import constants
import errors.database_errors as DbErrors
import gspread

"""
Example Table
"""


class ExmapleTable(BaseTable):
    """A class to manipulate the Example table in the database"""

    _db: CoreDatabase
    _worksheet: gspread.Worksheet

    def __init__(self, db: CoreDatabase):
        """Initialize the Example Table class"""
        super().__init__(
            db, constants.LEAGUE_DB_TAB_EXAMPLE, ExampleRecord, ExampleFields
        )

    async def create_example_record(
        self, example_a: str, example_b: str
    ) -> ExampleRecord:
        """Create a new Example record"""
        # Check for existing records to avoid duplication
        existing_record = await self.get_example_records(
            example_a=example_a, example_b=example_b
        )
        if existing_record:
            raise DbErrors.EmlRecordAlreadyExists(
                f"Example record already exists: {existing_record.to_dict()}"
            )
        # Create the new record
        record_list = [None] * len(ExampleFields)
        record_list[ExampleFields.example_a] = example_a
        record_list[ExampleFields.example_b] = example_b
        new_record = await self.create_record(ExampleRecord, record_list)
        # Insert the new record into the "database"
        await self.insert_record(new_record)
        return new_record

    async def update_example_record(self, record: ExampleRecord):
        """Update an existing Example record"""
        return await self.update_record(record)

    async def delete_example_record(self, record: ExampleRecord):
        """Delete an existing Example record"""
        record_id = await record.get_field(ExampleFields.record_id)
        return await self.delete_record(record_id)

    async def get_example_records(
        self, record_id: str = None, example_a: str = None, example_b: str = None
    ) -> ExampleRecord:
        """Get an existing Example record"""
        if record_id is None and example_a is None and example_b is None:
            raise ValueError(
                "At least one of 'record_id', 'example_a', or 'example_b' must be provided"
            )
        table = await self.get_table_data()
        for row in table:
            if table.index(row) == 0:
                continue
            if (
                (
                    not record_id
                    or str(record_id).casefold()
                    == str(row[ExampleFields.record_id]).casefold()
                )
                and (
                    not example_a
                    or str(example_a).casefold()
                    == str(row[ExampleFields.example_a]).casefold()
                )
                and (
                    not example_b
                    or str(example_b).casefold()
                    == str(row[ExampleFields.example_b]).casefold()
                )
            ):
                existing_record = ExampleRecord(row)
                return existing_record
        return None
