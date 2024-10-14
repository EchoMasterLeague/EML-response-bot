from database.base_table import BaseTable
from database.database_core import CoreDatabase
from database.enums import Bool
from database.fields import ConstantsFields
from database.records import ConstantsRecord
import constants
import gspread
import logging

logger = logging.getLogger(__name__)

"""
Constants Table
"""


class ConstantsTable(BaseTable):
    """A class to manipulate the Constants table in the database"""

    _db: CoreDatabase
    _worksheet: gspread.Worksheet

    def __init__(self, db: CoreDatabase):
        """Initialize the ConstantsLock Table class"""
        super().__init__(
            db,
            constants.LEAGUE_DB_TAB_CONSTANTS,
            ConstantsRecord,
            ConstantsFields,
        )
    async def get_constants_records(
        self, name: str = None
    ) -> list[ConstantsRecord]:
        """Get an existing Constants record"""
        # Walk the table
        table = await self.get_table_data()
        existing_records = []
        for row in table[1:]:  # skip header row
            # Check for matched record
            if (
                (
                    not name
                    or str(name).casefold()
                    == str(row[ConstantsFields.name]).casefold()
                )
            ):
                # Add matched record
                existing_record = ConstantsRecord(row)
                existing_records.append(existing_record)
        # Return matched records
        return existing_records
