from database.database_full import FullDatabase
from utils import discord_helpers, general_helpers
import discord
import logging

logger = logging.getLogger(__name__)


async def system_list_cache(database: FullDatabase, interaction: discord.Interaction):
    """List local cache"""
    try:
        await interaction.response.defer()
        #######################################################################
        #                               RECORDS                               #
        #######################################################################
        # Cache Times
        cache_times = await database.core_database.get_cache_times()

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################
        # Normalize Cache Times
        normalized_cache_times = {}
        for key, value in cache_times.items():
            normalized_cache_times[key] = await general_helpers.iso_timestamp(
                int(value)
            )

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        response_dictionary = normalized_cache_times
        response_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(response_dictionary), language="json"
        )
        await discord_helpers.final_message(
            interaction=interaction,
            message="\n".join(
                [
                    f"Cache Refresh Times:",
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
