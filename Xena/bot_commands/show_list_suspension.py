from database.database_full import FullDatabase
from database.fields import SuspensionFields
from utils import discord_helpers, general_helpers
import datetime
import discord


async def show_list_suspension(
    database: FullDatabase, interaction: discord.Interaction
):
    """Show all Players on suspension"""
    try:
        await interaction.response.defer()
        #######################################################################
        #                               RECORDS                               #
        #######################################################################
        # Suspension
        suspensions = await database.table_suspension.get_suspension_records(
            expires_after=datetime.datetime.now().timestamp()
        )
        assert suspensions, "No players on suspension."
        #######################################################################
        #                             PROCESSING                              #
        #######################################################################
        suspension_players = {}
        for suspension in suspensions:
            player_discord_id = await suspension.get_field(SuspensionFields.player_id)
            player_member = await discord_helpers.member_from_discord_id(
                guild=interaction.guild, discord_id=player_discord_id
            )
            player_name = await suspension.get_field(SuspensionFields.vw_player)
            player_name = (
                f"{player_member.global_name}({player_member.id})"
                if player_member
                else player_name
            )
            expires_at = await suspension.get_field(SuspensionFields.expires_at)
            suspension_players[player_name] = f"Expiration: {expires_at})"

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        response_dictionary = suspension_players
        response_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(response_dictionary), "json"
        )
        await discord_helpers.final_message(
            interaction=interaction,
            message="\n".join(
                [
                    f"Players on suspension:",
                    f"{response_code_block}",
                ]
            ),
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
