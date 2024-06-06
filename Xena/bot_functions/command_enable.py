from database.database_full import FullDatabase
from utils import discord_helpers
import discord


async def command_enable(
    database: FullDatabase, interaction: discord.Interaction, command_name: str
):
    """Enable a command"""
    try:
        # Defer Response
        interaction.response.defer()
        # Existing Records
        records = await database.table_command_lock.get_command_lock_records(
            command_name=command_name
        )
        record = records[0] if records else None
        if not record:
            # Create Record
            await database.table_command_lock.create_command_lock_record(
                command_name, is_allowed=True
            )
        else:
            # Update Record
            await record.set_field("is_allowed", True)
            await database.table_command_lock.update_command_lock_record(record)
        # Response
        await discord_helpers.final_message(
            interaction, f"Command `{command_name}` enabled."
        )
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
