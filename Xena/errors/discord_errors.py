class EmlDiscordException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


### Guild ###


class EmlDiscordGuildNotFoundException(EmlDiscordException):
    def __init__(self, message="Guild not found"):
        self.message = message
        super().__init__(self.message)


### Guild Role ###


class EmlDiscordGuildRoleNotFoundException(EmlDiscordException):
    def __init__(self, message="Guild Role not found"):
        self.message = message
        super().__init__(self.message)


class EmlDiscordGuildRoleExistsException(EmlDiscordException):
    def __init__(self, message="Guild Role already exists"):
        self.message = message
        super().__init__(self.message)


class EmlDiscordGuildRoleCreateException(EmlDiscordException):
    def __init__(self, message="Guild Role could not be created"):
        self.message = message
        super().__init__(self.message)


class EmlDiscordGuildRoleDeleteException(EmlDiscordException):
    def __init__(self, message="Guild Role could not be deleted"):
        self.message = message
        super().__init__(self.message)


### Member ###


class EmlDiscordMemberNotFoundException(EmlDiscordException):
    def __init__(self, message="Member not found"):
        self.message = message
        super().__init__(self.message)


### Member Role ###


class EmlDiscordMemberRoleNotFoundException(EmlDiscordException):
    def __init__(self, message="Member role not found"):
        self.message = message
        super().__init__(self.message)


class EmlDiscordMemberRoleExistsException(EmlDiscordException):
    def __init__(self, message="Member role already exists"):
        self.message = message
        super().__init__(self.message)


class EmlDiscordMemberRoleAssignmentException(EmlDiscordException):
    def __init__(self, message="Member role could not be assigned"):
        self.message = message
        super().__init__(self.message)


class EmlDiscordMemberRoleRemovalException(EmlDiscordException):
    def __init__(self, message="Member role could not be removed"):
        self.message = message
        super().__init__(self.message)
