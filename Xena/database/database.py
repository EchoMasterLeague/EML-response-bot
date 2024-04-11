import constants
import gspread


class Database:
    """Google Sheets (pseudo-) Database

    This class is a pseudo-database that uses Google Sheets as a backend. It is
    designed to be used with the `gspread` library.

    Attributes:
        gs_client (gspread.Client): The Google Sheets client to use
        spreadsheet (gspread.Spreadsheet): The Google Sheets spreadsheet to use
    """

    def __init__(self, gs_client: gspread.Client):
        """Initialize the Database class"""
        try:
            self.gs_client: gspread.client.Client = gs_client
            self.table_spreadsheet: gspread.spreadsheet.Spreadsheet = (
                gs_client.open_by_url(constants.LEAGUE_DB_SPREADSHEET_URL)
            )
            self.view_spreadsheet: gspread.spreadsheet.Spreadsheet = (
                gs_client.open_by_url(constants.LEAGUE_VIEW_SPREADSHEET_URL)
            )
        except gspread.SpreadsheetNotFound as error:
            print(f"Spreadsheet not found: {error}")
            self.table_spreadsheet = None

    def get_db_worksheet(self, title: str) -> gspread.Worksheet:
        """Get a worksheet from the DB spreadsheet by title"""
        try:
            worksheet = self.table_spreadsheet.worksheet(title)
            return worksheet
        except gspread.WorksheetNotFound as error:
            print(f"Worksheet not found: {error}")
            return None

    def get_view_worksheet(self, title: str) -> gspread.Worksheet:
        """Get a worksheet from the View spreadsheet by title"""
        try:
            worksheet = self.view_spreadsheet.worksheet(title)
            return worksheet
        except gspread.WorksheetNotFound as error:
            print(f"Worksheet not found: {error}")
            return None
