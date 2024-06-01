from database.database_full import FullDatabase
from utils import discord_helpers, general_helpers
import discord


class ManageSystem:
    """EML System Management"""

    def __init__(self, database: FullDatabase):
        self._db = database

    async def list_pending_writes(self, interaction: discord.Interaction):
        """List pending write operations"""
        try:
            await interaction.response.defer()  # This could take a while
            pending_writes = await self._db.core_database.get_pending_writes()
            pending_writes_json = await general_helpers.format_json(pending_writes)
            code_block = await discord_helpers.code_block(
                pending_writes_json, language="json"
            )
            message = f"Pending writes: {code_block}"
            return await discord_helpers.final_message(interaction, message)
        except Exception as error:
            return await discord_helpers.error_message(interaction, error)

    async def list_local_cache(self, interaction: discord.Interaction):
        """List local cache"""
        try:
            await interaction.response.defer()  # This could take a while
            cache_times = await self._db.core_database.get_cache_times()
            cache_times_json = await general_helpers.format_json(cache_times)
            code_block = await discord_helpers.code_block(
                cache_times_json, language="json"
            )
            message = f"Local cache last update times: {code_block}"
            return await discord_helpers.final_message(interaction, message)
        except Exception as error:
            return await discord_helpers.error_message(interaction, error)
