from bot_dialogues import choices
from database.database_full import FullDatabase
from database.fields import TeamInviteFields, PlayerFields, TeamPlayerFields, TeamFields
from database.records import TeamRecord
from utils import discord_helpers, database_helpers
import constants
import datetime
import discord
import utils.general_helpers as bot_helpers


class ManageMatches:
    """EML Match Management"""

    def __init__(self, database: FullDatabase):
        self._db = database

    async def send_match_invite(
        self, interaction: discord.Interaction, opposing_team_name: str, date: str
    ):
        pass

    async def accept_match_invite(self, interaction: discord.Interaction):
        pass

    async def revoke_match_invite(self, interaction: discord.Interaction):
        pass

    async def send_result_invite(
        self,
        interaction: discord.Interaction,
        opposing_team_name: str,
        round_one_scores: str,
        round_two_scores: str,
        round_three_scores: str = None,
    ):
        pass

    async def accept_result_invite(self, interaction: discord.Interaction):
        pass

    async def revoke_result_invite(self, interaction: discord.Interaction):
        pass
