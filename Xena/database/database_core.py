from database.enums import WriteOperations
import constants
import errors.database_errors as DbErrors
import gspread
import time


class CoreDatabase:
    """Google Sheets (pseudo-) Database

    This class is a pseudo-database that uses Google Sheets as a backend. It is
    designed to be used with the `gspread` library.

    Attributes:
        _gs_client (gspread.Client): The Google Sheets client to use
        _db_spreadsheet (gspread.Spreadsheet): The Google Sheets spreadsheet to use as a database
        _db_local_cache (dict): A cache of worksheets to reduce API calls
        _db_write_queue (dict): A queue of write operations to commit to the database
    """

    def __init__(self, gs_client: gspread.Client):
        """Initialize the Database class"""
        self._gs_client = gs_client
        self._worksheets: dict[str, gspread.Worksheet] = {}
        self._db_cache_pull_times: dict[str, float] = {}
        self._db_local_cache: dict[list[list[int | float | str | None]]] = {}
        self._db_write_queue: dict[list[list[int | float | str | None]]] = {}
        try:
            self._db_spreadsheet = gs_client.open_by_url(
                constants.LEAGUE_DB_SPREADSHEET_URL
            )
        except gspread.SpreadsheetNotFound as error:
            raise DbErrors.EmlSpreadsheetDoesNotExist(f"Spreadsheet not found: {error}")

    def create_table_worksheet(self, title: str) -> gspread.Worksheet:
        """Create a new worksheet in the DB spreadsheet"""
        try:
            worksheet = self._db_spreadsheet.add_worksheet(
                title,
                rows=constants.LEAGUE_DB_SPREADSHEET_DEFAULT_ROWS,
                cols=constants.LEAGUE_DB_SPREADSHEET_DEFAULT_COLS,
            )
            worksheet.format("A1:Z1", {"textFormat": {"bold": True}})
            worksheet.freeze(rows=1)
        except gspread.WorksheetNotFound as error:
            raise DbErrors.EmlWorksheetCreateError(f"Worsheet not created: {error}")
        return worksheet

    def get_table_worksheet(self, table_name: str) -> gspread.Worksheet:
        """Get a worksheet from the DB spreadsheet by title"""
        try:
            if table_name not in self._worksheets:
                print(f"Getting Worksheet: {table_name} (not cached)")
                self._worksheets[table_name] = self._db_spreadsheet.worksheet(
                    table_name
                )
        except gspread.WorksheetNotFound as error:
            raise DbErrors.EmlWorksheetDoesNotExist(f"Worksheet not found: {error}")
        return self._worksheets[table_name]

    async def get_table_data(
        self, table_name: str
    ) -> list[list[int | float | str | None]]:
        """Get all the data from a worksheet"""
        # write any pending changes to the spreadsheet
        await self.commit_all_writes()
        # get the data from the worksheet if needed
        is_cached = (
            table_name in self._db_local_cache
            and table_name in self._db_cache_pull_times
        )
        is_stale = (
            table_name in self._db_cache_pull_times
            and (time.time() - self._db_cache_pull_times[table_name])
            > constants.LEAGUE_DB_CACHE_DURATION_SECONDS
        )
        if not is_cached or is_stale:
            reason = "cache stale" if is_stale else "not cached"
            print(f"Getting Table: {table_name} ({reason})")
            worksheet = self.get_table_worksheet(table_name)
            self._db_local_cache[table_name] = worksheet.get_all_values()
            self._db_cache_pull_times[table_name] = time.time()
        return self._db_local_cache[table_name]

    async def append_row(
        self, table_name: str, row_data: list[int | float | str | None]
    ) -> None:
        """Insert a record into a worksheet"""
        # Add the write operation to the queue
        if table_name not in self._db_write_queue:
            self._db_write_queue[table_name] = []
        queued_write = [WriteOperations.INSERT] + row_data
        self._db_write_queue[table_name] += [queued_write]
        # Update the local cache
        if table_name in self._db_local_cache:
            self._db_local_cache[table_name] += [row_data]
        # write any pending changes to the spreadsheet
        await self.commit_all_writes()

    async def update_row(
        self, table_name: str, row_data: list[int | float | str | None]
    ) -> None:
        """Update a record in a worksheet"""
        # Add the write operation to the queue
        if table_name not in self._db_write_queue:
            self._db_write_queue[table_name] = []
        queued_write = [WriteOperations.UPDATE] + row_data
        self._db_write_queue[table_name] += [queued_write]
        # Update the local cache
        id = row_data[0]
        if table_name in self._db_local_cache:
            for i, row in enumerate(self._db_local_cache[table_name]):
                if row[0] == id:
                    self._db_local_cache[table_name][i] = row_data
                    break
        # write any pending changes to the spreadsheet
        await self.commit_all_writes()

    async def delete_row(self, table_name: str, record_id: str) -> None:
        """Delete a record from a worksheet"""
        # Add the write operation to the write queue
        if table_name not in self._db_write_queue:
            self._db_write_queue[table_name] = []
        queued_write = [WriteOperations.DELETE, record_id]
        self._db_write_queue[table_name] += [queued_write]
        # Update the local cache
        if table_name in self._db_local_cache:
            for i, row in enumerate(self._db_local_cache[table_name]):
                if row[0] == record_id:
                    del self._db_local_cache[table_name][i]
                    break
        # write any pending changes to the spreadsheet
        await self.commit_all_writes()

    async def commit_single_write(
        self,
        worksheet: gspread.Worksheet,
        operation: WriteOperations,
        record_id: str,
        row_data: list[int | float | str | None] = None,
    ) -> None:
        """Commit a single write operation to the worksheet"""
        if operation == WriteOperations.INSERT:
            print(f"Insert in {worksheet.title} (write)")
            worksheet.append_row(row_data, table_range="A1")
        elif operation == WriteOperations.UPDATE:
            print(f"Update in {worksheet.title} (read and write)")
            cell = worksheet.find(record_id, in_column=1)
            worksheet.update(f"A{cell.row}", [row_data])
        elif operation == WriteOperations.DELETE:
            print(f"Delete in {worksheet.title} (read and write)")
            cell = worksheet.find(record_id, in_column=1)
            worksheet.delete_rows(cell.row)

    async def commit_all_writes(self, table_name: str = None) -> None:
        """Commit the write queue to the database"""
        tables = self._db_write_queue.keys() if table_name is None else [table_name]
        writes: list[list[int | float | str | None]]
        for table_name, writes in self._db_write_queue.items():
            if table_name not in tables:
                continue
            worksheet = self.get_table_worksheet(table_name)
            while writes:
                write = writes[0]
                operation = write[0]
                record_id = write[1]
                row_data = write[1:]
                try:
                    await self.commit_single_write(
                        worksheet, operation, record_id, row_data
                    )
                    writes.pop(0)
                except Exception as error:
                    print(f"Failed to commit write: {error}")
                    time.sleep(1)
        # Remove synced tables from the write queue
        for table_name in self._db_write_queue.keys():
            if self._db_write_queue[table_name] == []:
                del self._db_write_queue[table_name]

    async def get_pending_writes(
        self,
    ) -> dict[str, list[list[int | float | str | None]]]:
        """Get all pending write operations"""
        return self._db_write_queue

    async def get_cache_times(
        self,
    ) -> dict[str, float]:
        """Get all cache times"""
        return self._db_cache_pull_times
