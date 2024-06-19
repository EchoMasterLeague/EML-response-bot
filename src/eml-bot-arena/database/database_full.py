from database.database_core import CoreDatabase
from database.table_command_lock import CommandLockTable
from database.table_cooldown import CooldownTable
from database.table_league_sub_match import LeagueSubMatchTable
from database.table_league_sub_match_invite import LeagueSubMatchInviteTable
from database.table_match import MatchTable
from database.table_match_invite import MatchInviteTable
from database.table_match_result_invite import MatchResultInviteTable
from database.table_player import PlayerTable
from database.table_suspension import SuspensionTable
from database.table_team import TeamTable
from database.table_team_invite import TeamInviteTable
from database.table_team_player import TeamPlayerTable
from database.table_vw_roster import VwRosterTable
import logging

logger = logging.getLogger(__name__)


class FullDatabase:
    """Holds all the tables"""

    def __init__(self, core_database: CoreDatabase):
        """Initialize the Database class"""
        self.core_database = core_database
        self.table_command_lock = CommandLockTable(core_database)
        self.table_cooldown = CooldownTable(core_database)
        self.table_league_sub_match = LeagueSubMatchTable(core_database)
        self.table_league_sub_match_invite = LeagueSubMatchInviteTable(core_database)
        self.table_match = MatchTable(core_database)
        self.table_match_invite = MatchInviteTable(core_database)
        self.table_match_result_invite = MatchResultInviteTable(core_database)
        self.table_player = PlayerTable(core_database)
        self.table_suspension = SuspensionTable(core_database)
        self.table_team = TeamTable(core_database)
        self.table_team_invite = TeamInviteTable(core_database)
        self.table_team_player = TeamPlayerTable(core_database)
        self.table_vw_roster = VwRosterTable(core_database)
