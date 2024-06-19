from database.database_full import FullDatabase
from database.fields import PlayerFields
from utils import discord_helpers, player_helpers, general_helpers
import discord
import logging

logger = logging.getLogger(__name__)


async def league_sub_unregister(
    database: FullDatabase, interaction: discord.Interaction
):
    """Unregister as a League Substitute"""
    try:
        #######################################################################
        #                               RECORDS                               #
        #######################################################################
        # "My" Player
        my_player_records = await database.table_player.get_player_records(
            discord_id=interaction.user.id
        )
        assert my_player_records, "You are not registered as a player."
        my_player_record = my_player_records[0]
        assert await my_player_record.get_field(
            PlayerFields.is_sub
        ), "You are not a League Substitute."

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################

        # Update Player record
        await my_player_record.set_field(PlayerFields.is_sub, False)
        await database.table_player.update_player_record(my_player_record)

        # Remove League Substitute role
        await discord_helpers.member_remove_league_sub_role(interaction.user)

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        player_name = await my_player_record.get_field(PlayerFields.player_name)
        response_dictionary = {
            "player": f"{await my_player_record.get_field(PlayerFields.player_name)}",
            "region": f"{await my_player_record.get_field(PlayerFields.region)}",
            "is_league_sub": f"{await my_player_record.get_field(PlayerFields.is_sub)}",
            "team": None,
            "team_role": None,
        }

        response_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(response_dictionary), "json"
        )
        await discord_helpers.final_message(
            interaction=interaction,
            message="\n".join(
                [
                    f"Player `{player_name}` unregistered from League Substitue:",
                    f"{response_code_block}",
                ]
            ),
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################
        my_player_mention = f"{await discord_helpers.role_mention(guild=interaction.guild, discord_id=await my_player_record.get_field(PlayerFields.discord_id))}"
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"{my_player_mention} has unregistered from League Substitute.",
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.fail_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
