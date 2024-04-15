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


class EmlWorksheetCreate(EmlDatabaseException):
    def __init__(self, message="Error creating worksheet"):
        self.message = message
        super().__init__(self.message)


class EmlWorksheetRead(EmlDatabaseException):
    def __init__(self, message="Error reading worksheet"):
        self.message = message
        super().__init__(self.message)


class EmlWorksheetWrite(EmlDatabaseException):
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


### Player ###


class EmlPlayerNotFound(EmlDatabaseException):
    def __init__(self, message="Player not found"):
        self.message = message
        super().__init__(self.message)


class EmlPlayerAlreadyExists(EmlDatabaseException):
    def __init__(self, message="Player already exists"):
        self.message = message
        super().__init__(self.message)


class EmlPlayerRegionNotFound(EmlDatabaseException):
    def __init__(self, message="Region not found"):
        self.message = message
        super().__init__(self.message)


class EmlPlayerRegionMismatch(EmlDatabaseException):
    def __init__(self, message="Region mismatch"):
        self.message = message
        super().__init__(self.message)


### Team ###


class EmlTeamNotFound(EmlDatabaseException):
    def __init__(self, message="Team not found"):
        self.message = message
        super().__init__(self.message)


class EmlTeamNotCreated(EmlDatabaseException):
    def __init__(self, message="Team not created"):
        self.message = message
        super().__init__(self.message)


class EmlTeamAlreadyExists(EmlDatabaseException):
    def __init__(self, message="Team already exists"):
        self.message = message
        super().__init__(self.message)


class EmlTeamFull(EmlDatabaseException):
    def __init__(self, message="Team is full"):
        self.message = message
        super().__init__(self.message)


class EmlTeamSizeTooSmall(EmlDatabaseException):
    def __init__(self, message="Team size is too small"):
        self.message = message
        super().__init__(self.message)


class EmlTeamStatusNotFound(EmlDatabaseException):
    def __init__(self, message="Team status not found"):
        self.message = message
        super().__init__(self.message)


### Team Player ###


class EmlTeamPlayerNotCreated(EmlDatabaseException):
    def __init__(self, message="Team Player not created"):
        self.message = message
        super().__init__(self.message)


class EmlTeamPlayerNotFound(EmlDatabaseException):
    def __init__(self, message="Team Player not found"):
        self.message = message
        super().__init__(self.message)


class EmlTeamPlayerAlreadyExists(EmlDatabaseException):
    def __init__(self, message="Team Player already exists"):
        self.message = message
        super().__init__(self.message)


class EmlTeamPlayerNotOnTeam(EmlDatabaseException):
    def __init__(self, message="Player is not on a Team"):
        self.message = message
        super().__init__(self.message)


class EmlTeamPlayerAlreadyOnTeam(EmlDatabaseException):
    def __init__(self, message="Player is already on a Team"):
        self.message = message
        super().__init__(self.message)


class EmlTeamPlayerIsNotCaptain(EmlDatabaseException):
    def __init__(self, message="Player is not a Team captain"):
        self.message = message
        super().__init__(self.message)


class EmlTeamPlayerIsCaptain(EmlDatabaseException):
    def __init__(self, message="Player is a captain on a Team"):
        self.message = message
        super().__init__(self.message)


class EmlTeamPlayerCoCapteanAlreadyExists(EmlDatabaseException):
    def __init__(self, message="Team already has a Co-Captain"):
        self.message = message
        super().__init__(self.message)
