from database.database_full import FullDatabase
from utils import discord_helpers, general_helpers
import discord


async def system_list_writes(database: FullDatabase, interaction: discord.Interaction):
    """List pending write operations"""
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
        pending_writes = await database.core_database.get_pending_writes()
        pending_writes_json = await general_helpers.format_json(pending_writes)
        code_block = await discord_helpers.code_block(
            pending_writes_json, language="json"
        )
        message = f"Pending writes: {code_block}"
        return await discord_helpers.final_message(interaction, message)

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
