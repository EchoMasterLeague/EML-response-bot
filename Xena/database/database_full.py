from database.database_core import CoreDatabase
from database.table_command_lock import CommandLockTable
from database.table_cooldown import CooldownTable
from database.table_invite import InviteTable
from database.table_player import PlayerTable
from database.table_team import TeamTable
from database.table_team_player import TeamPlayerTable


class FullDatabase:
    """Holds all the tables"""

    def __init__(self, core_database: CoreDatabase):
        """Initialize the Database class"""
        self._database = core_database
        self.table_command_lock = CommandLockTable(core_database)
        self.table_cooldown = CooldownTable(core_database)
        self.table_invite = InviteTable(core_database)
        self.table_player = PlayerTable(core_database)
        self.table_team = TeamTable(core_database)
        self.table_team_player = TeamPlayerTable(core_database)
