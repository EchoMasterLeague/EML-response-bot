from database.database_full import FullDatabase
from database.fields import CooldownFields
from utils import discord_helpers, general_helpers
import datetime
import discord
import logging

logger = logging.getLogger(__name__)


async def show_list_cooldown(database: FullDatabase, interaction: discord.Interaction):
    """Show all Players on cooldown"""
    try:
        await interaction.response.defer()
        #######################################################################
        #                               RECORDS                               #
        #######################################################################
        # Cooldown
        cooldowns = await database.table_cooldown.get_cooldown_records(
            expires_after=datetime.datetime.now().timestamp()
        )
        assert cooldowns, "No players on cooldown."
        #######################################################################
        #                             PROCESSING                              #
        #######################################################################
        cooldown_players = {}
        for cooldown in cooldowns:
            player_name = await cooldown.get_field(CooldownFields.vw_player)
            former_team = await cooldown.get_field(CooldownFields.vw_old_team)
            created_at = await cooldown.get_field(CooldownFields.created_at)
            cooldown_players[player_name] = f"{former_team} ({created_at})"

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        response_dictionary = cooldown_players
        response_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(response_dictionary), "json"
        )
        await discord_helpers.final_message(
            interaction=interaction,
            message="\n".join(
                [
                    f"Players on cooldown:",
                    f"{response_code_block}",
                ]
            ),
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################

    # Errors
    except AssertionError as message:
        await discord_helpers.fail_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
