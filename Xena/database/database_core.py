import constants
import gspread
import errors.database_errors as DbErrors


class CoreDatabase:
    """Google Sheets (pseudo-) Database

    This class is a pseudo-database that uses Google Sheets as a backend. It is
    designed to be used with the `gspread` library.

    Attributes:
        gs_client (gspread.Client): The Google Sheets client to use
        spreadsheet (gspread.Spreadsheet): The Google Sheets spreadsheet to use
    """

    def __init__(self, gs_client: gspread.Client):
        """Initialize the Database class"""
        self.gs_client = gs_client
        try:
            self.table_spreadsheet = gs_client.open_by_url(
                constants.LEAGUE_DB_SPREADSHEET_URL
            )
            self.view_spreadsheet = gs_client.open_by_url(
                constants.LEAGUE_VIEW_SPREADSHEET_URL
            )
        except gspread.SpreadsheetNotFound as error:
            raise DbErrors.EmlSpreadsheetDoesNotExist(f"Spreadsheet not found: {error}")

    def create_db_worksheet(self, title: str) -> gspread.Worksheet:
        """Create a new worksheet in the DB spreadsheet"""
        try:
            worksheet = self.table_spreadsheet.add_worksheet(
                title,
                rows=constants.LEAGUE_DB_SPREADSHEET_DEFAULT_ROWS,
                cols=constants.LEAGUE_DB_SPREADSHEET_DEFAULT_COLS,
            )
            worksheet.format("A1:Z1", {"textFormat": {"bold": True}})
            worksheet.freeze(rows=1)
        except gspread.WorksheetNotFound as error:
            raise DbErrors.EmlWorksheetCreateError(f"Worsheet not created: {error}")
        return worksheet

    def get_db_worksheet(self, title: str) -> gspread.Worksheet:
        """Get a worksheet from the DB spreadsheet by title"""
        try:
            worksheet = self.table_spreadsheet.worksheet(title)
        except gspread.WorksheetNotFound as error:
            raise DbErrors.EmlWorksheetDoesNotExist(f"Worksheet not found: {error}")
        return worksheet

    def get_view_worksheet(self, title: str) -> gspread.Worksheet:
        """Get a worksheet from the View spreadsheet by title"""
        try:
            worksheet = self.view_spreadsheet.worksheet(title)

        except gspread.WorksheetNotFound as error:
            raise DbErrors.EmlWorksheetDoesNotExist(f"Worksheet not found: {error}")
        return worksheet
