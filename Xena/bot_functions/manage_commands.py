from database.database_full import FullDatabase
from database.fields import CommandLockFields
import discord


class ManageCommands:
    """EML Command Management"""

    def __init__(self, database: FullDatabase):
        self._db = database

    async def is_command_allowed(
        self,
        interaction: discord.Interaction,
        command_name: str,
    ):
        """Command availablity check"""
        try:
            command_lock_record = (
                await self._db.table_command_lock.get_command_lock_record(
                    command_name=command_name
                )
            )
            if not command_lock_record:
                command_lock_record = (
                    await self._db.table_command_lock.create_command_lock_record(
                        command_name=command_name, is_allowed=True
                    )
                )
            assert command_lock_record, "CommandLock record not found"
            is_allowed = await command_lock_record.get_field(
                CommandLockFields.is_allowed
            )
            assert is_allowed, "Command is not allowed"
            return True
        except AssertionError as error:
            message = f"Command `{command_name}` is currently disabled"
            await interaction.response.send_message(message)
        return False
