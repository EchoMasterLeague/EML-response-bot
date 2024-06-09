from database.database_full import FullDatabase
from database.fields import CommandLockFields
from utils import discord_helpers
import discord


async def command_is_enabled(
    database: FullDatabase,
    interaction: discord.Interaction,
    default_enabled: bool = True,
    skip_db: bool = False,
):
    """Command availablity check"""
    try:
        command_name = interaction.command.name
        if skip_db:
            return default_enabled

        #######################################################################
        #                               RECORDS                               #
        #######################################################################
        # Command Lock
        command_lock_records = (
            await database.table_command_lock.get_command_lock_records(
                command_name=command_name
            )
        )
        record = command_lock_records[0] if command_lock_records else None
        if not record:
            record = await database.table_command_lock.create_command_lock_record(
                command_name, True
            )

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################
        # Command Availability
        is_allowed = default_enabled
        if record:
            is_allowed = await record.get_field(CommandLockFields.is_allowed)

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        # Command Disabled
        if is_allowed == False:
            await discord_helpers.final_message(
                interaction, f"Command `{command_name}`is currently disabled."
            )
            return False
        # Command Enabled
        return True

    # Errors
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
    return False