from database.database_full import FullDatabase
from utils import discord_helpers, general_helpers
import discord
from utils import discord_helpers, general_helpers


async def admin_generate_uuid(database: FullDatabase, interaction: discord.Interaction):
    """Generate UUID"""
    try:
        await interaction.response.defer(ephemeral=True)
        #######################################################################
        #                               RECORDS                               #
        #######################################################################

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        now_epoch = await general_helpers.epoch_timestamp()
        monday_epoch = await general_helpers.upcoming_monday()
        response_dictionary = {
            "uuid_1": await general_helpers.random_id(),
            "uuid_2": await general_helpers.random_id(),
            "now_epoch": now_epoch,
            "now_utc": await general_helpers.iso_timestamp(now_epoch),
            "now_eml": f"{await general_helpers.eml_date(now_epoch)} {await general_helpers.eml_time(now_epoch)}",
            "monday_epoch": monday_epoch,
            "monday_utc": await general_helpers.iso_timestamp(monday_epoch),
            "monday_eml": f"{await general_helpers.eml_date(monday_epoch)} {await general_helpers.eml_time(monday_epoch)}",
        }
        response_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(response_dictionary), "json"
        )
        await discord_helpers.final_message(
            interaction=interaction,
            message="\n".join(
                [
                    f"UUID to use as a DB record_id:",
                    f"{response_code_block}",
                ]
            ),
            ephemeral=True,
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message, ephemeral=True)
    except Exception as error:
        await discord_helpers.error_message(interaction, error, ephemeral=True)
