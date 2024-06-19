class EmlDatabaseException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


### Google Sheets Backend###


class EmlSpreadsheetDoesNotExist(EmlDatabaseException):
    def __init__(self, message="Spreadsheet does not exist"):
        self.message = message
        super().__init__(self.message)


class EmlWorksheetDoesNotExist(EmlDatabaseException):
    def __init__(self, message="Worksheet does not exist"):
        self.message = message
        super().__init__(self.message)


class EmlWorksheetCreateError(EmlDatabaseException):
    def __init__(self, message="Error creating worksheet"):
        self.message = message
        super().__init__(self.message)


class EmlWorksheetReadError(EmlDatabaseException):
    def __init__(self, message="Error reading worksheet"):
        self.message = message
        super().__init__(self.message)


class EmlWorksheetWriteError(EmlDatabaseException):
    def __init__(self, message="Error writing to worksheet"):
        self.message = message
        super().__init__(self.message)


### Database General ###


class EmlRecordNotFound(EmlDatabaseException):
    def __init__(self, message="Record not found"):
        self.message = message
        super().__init__(self.message)


class EmlRecordAlreadyExists(EmlDatabaseException):
    def __init__(self, message="Record already exists"):
        self.message = message
        super().__init__(self.message)
