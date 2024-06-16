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
        # Pending Writes
        pending_writes = await database.core_database.get_pending_writes()

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################
        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        response_dictionary = pending_writes
        response_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(response_dictionary), language="json"
        )
        await discord_helpers.final_message(
            interaction=interaction,
            message="\n".join(
                [
                    f"Pending writes:",
                    f"{response_code_block}",
                ]
            ),
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
