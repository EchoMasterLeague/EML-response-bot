from database.database_full import FullDatabase
from utils import discord_helpers
import discord


async def command_is_enabled(database: FullDatabase, interaction: discord.Interaction):
    """Command availablity check"""
    try:
        command_name = interaction.command.name
        is_allowed = await database.table_command_lock.ensure_command_allowance(
            command_name
        )
        assert is_allowed, f"Command `{command_name}`is currently disabled."
        return True
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
    return False
