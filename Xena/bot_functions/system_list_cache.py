from database.database_full import FullDatabase
from utils import discord_helpers, general_helpers
import discord


async def system_list_cache(database: FullDatabase, interaction: discord.Interaction):
    """List local cache"""
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
        cache_times = await database.core_database.get_cache_times()
        normalized_cache_times = {}
        for key, value in cache_times.items():
            normalized_cache_times[key] = await general_helpers.iso_timestamp(
                int(value)
            )
        cache_times_json = await general_helpers.format_json(normalized_cache_times)
        code_block = await discord_helpers.code_block(cache_times_json, language="json")
        message = f"Local cache last update times: {code_block}"
        return await discord_helpers.final_message(interaction, message)

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
