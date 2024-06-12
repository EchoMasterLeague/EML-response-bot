from database.database_full import FullDatabase
from database.fields import CommandLockFields
from utils import discord_helpers
import constants
import discord


async def command_is_enabled(
    database: FullDatabase,
    interaction: discord.Interaction,
    default_enabled: bool = True,
    skip_db: bool = False,
    skip_channel: bool = False,
    require_admin: bool = False,
):
    """Command availablity check"""
    try:
        command_name = interaction.command.name
        if skip_db:
            return default_enabled

        #######################################################################
        #                               RECORDS                               #
        #######################################################################
        if not skip_db:
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
        # Admin Check
        if require_admin:
            if not await discord_helpers.member_is_admin(interaction.user):
                await discord_helpers.final_message(
                    interaction=interaction,
                    message=f"Command `{command_name}` is only available to admins.",
                    ephemeral=True,
                )
                return False

        # Channel Availability
        if not skip_channel:
            bot_channel = await discord_helpers.get_guild_channel(
                interaction=interaction,
                channel_name=constants.DISCORD_CHANNEL_BOT_COMMANDS,
            )
            this_channel = interaction.channel
            if bot_channel != this_channel:
                await discord_helpers.final_message(
                    interaction=interaction,
                    message=f"Command `{command_name}` is only available in the channel {bot_channel.mention}.",
                    ephemeral=True,
                )
                return False

        # Command Availability
        is_allowed = default_enabled
        if record:
            is_allowed = await record.get_field(CommandLockFields.is_allowed)

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        # Command Disabled
        if not is_allowed:
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
