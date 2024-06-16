from database.database_full import FullDatabase
from database.fields import CommandLockFields
from utils import discord_helpers, general_helpers
import discord


async def command_disable(
    database: FullDatabase, interaction: discord.Interaction, command_name: str
):
    """Disable a command"""
    try:
        # Defer Response
        await interaction.response.defer()

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

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################
        if not record:
            # Create Record
            record = await database.table_command_lock.create_command_lock_record(
                command_name, is_allowed=False
            )
            assert record, f"Error: Command `{command_name}` could not be disabled."
        else:
            # Update Record
            await record.set_field(CommandLockFields.is_allowed, False)
            await database.table_command_lock.update_command_lock_record(record)

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        command_name = await record.get_field(CommandLockFields.command_name)
        response_dictionary = {
            "record_id": await record.get_field(CommandLockFields.record_id),
            "command_name": await record.get_field(CommandLockFields.command_name),
            "is_allowed": await record.get_field(CommandLockFields.is_allowed),
        }
        response_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(response_dictionary), "json"
        )
        await discord_helpers.final_message(
            interaction=interaction,
            message=(f"Command `{command_name}` disabled.\n{response_code_block}"),
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
