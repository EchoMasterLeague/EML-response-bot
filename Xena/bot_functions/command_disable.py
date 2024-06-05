from database.database_full import FullDatabase
from utils import discord_helpers
import discord


async def command_disable(
    database: FullDatabase, interaction: discord.Interaction, command_name: str
):
    """Disable a command"""
    try:
        interaction.response.defer()  # This could take a while
        records = await database.table_command_lock.get_command_lock_records(
            command_name=command_name
        )
        record = records[0] if records else None
        record = await database.table_command_lock.update_command_lock_record(
            record, is_allowed=False
        )
        message = f"Command `{command_name}` disabled."
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
