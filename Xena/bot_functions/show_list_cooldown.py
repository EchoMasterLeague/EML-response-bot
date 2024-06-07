from database.database_full import FullDatabase
from database.fields import CooldownFields
from utils import discord_helpers, general_helpers
import datetime
import discord


async def show_list_cooldown(database: FullDatabase, interaction: discord.Interaction):
    """Show all Players on cooldown"""
    try:
        await interaction.response.defer()
        #######################################################################
        #                               RECORDS                               #
        #######################################################################
        #######################################################################
        #                               OPTIONS                               #
        #######################################################################
        #######################################################################
        #                               CHOICE                                #
        #######################################################################
        #######################################################################
        #                             PROCESSING                              #
        #######################################################################
        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        #######################################################################
        #                               LOGGING                               #
        #######################################################################
        # Get Cooldown info
        cooldowns = await database.table_cooldown.get_cooldown_records(
            expires_after=datetime.datetime.now().timestamp()
        )
        assert cooldowns, "No players on cooldown."
        cooldown_players = {}
        for cooldown in cooldowns:
            player_name = await cooldown.get_field(CooldownFields.vw_player)
            former_team = await cooldown.get_field(CooldownFields.vw_old_team)
            created_at = await cooldown.get_field(CooldownFields.created_at)
            cooldown_players[player_name] = f"{former_team} ({created_at})"
        # Create Response
        message = await general_helpers.format_json(cooldown_players)
        message = await discord_helpers.code_block(message, language="json")
        message = f"Players on cooldown:\n{message}"
        return await discord_helpers.final_message(interaction, message)

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
