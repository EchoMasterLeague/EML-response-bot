from database.database_full import FullDatabase
from database.fields import CommandLockFields
import discord

from database.database_full import FullDatabase
from database.table_command_lock import CommandLockTable
import discord
from utils import discord_helpers


class ManageCommands:
    """EML Command Management"""

    def __init__(self, database: FullDatabase):
        self._db = database

    async def is_command_enabled(
        self,
        interaction: discord.Interaction,
        command_name: str = None,
    ):
        """Command availablity check"""
        try:
            command_name = command_name or interaction.command.name
            is_allowed = await self._db.table_command_lock.ensure_command_allowance(
                command_name
            )
            assert is_allowed, f"Command `{command_name}`is currently disabled."
            return True
        except AssertionError as message:
            await discord_helpers.final_message(interaction, message)
        except Exception as error:
            await discord_helpers.error_message(interaction, error)
        return False

    async def enable_command(self, interaction: discord.Interaction, command_name: str):
        """Enable a command"""
        try:
            interaction.response.defer()  # This could take a while
            record = await self._db.table_command_lock.get_command_lock_record(
                command_name=command_name
            )
            record = await self._db.table_command_lock.update_command_lock_record(
                record, is_allowed=True
            )
            message = f"Command `{command_name}` enabled."
            await discord_helpers.final_message(interaction, message)
        except Exception as error:
            await discord_helpers.error_message(interaction, error)

    async def disable_command(
        self, interaction: discord.Interaction, command_name: str
    ):
        """Disable a command"""
        try:
            interaction.response.defer()  # This could take a while
            record = await self._db.table_command_lock.get_command_lock_record(
                command_name=command_name
            )
            record = await self._db.table_command_lock.update_command_lock_record(
                record, is_allowed=False
            )
            message = f"Command `{command_name}` disabled."
            await discord_helpers.final_message(interaction, message)
        except Exception as error:
            await discord_helpers.error_message(interaction, error)
