from database.database_full import FullDatabase
from database.fields import PlayerFields
from utils import discord_helpers, player_helpers, general_helpers
import discord


async def player_unregister(
    database: FullDatabase,
    interaction: discord.Interaction,
):
    """Unregister a Player"""
    try:
        await interaction.response.defer()
        #######################################################################
        #                               RECORDS                               #
        #######################################################################
        # "My" Player
        my_player_records = await database.table_player.get_player_records(
            discord_id=interaction.user.id
        )
        assert my_player_records, "You are not registered."
        my_player_record = my_player_records[0]
        # "My" Team Player
        my_team_player_records = (
            await database.table_team_player.get_team_player_records(
                player_id=await my_player_record.get_field(PlayerFields.record_id)
            )
        )
        assert not my_team_player_records, "You must leave your team first."

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################

        # Remove Discord Roles
        await player_helpers.member_remove_player_role(
            await discord_helpers.member_from_discord_id(
                guild=interaction.guild,
                discord_id=await my_player_record.get_field(PlayerFields.discord_id),
            )
        )

        # Delete Player record
        await database.table_player.delete_player_record(my_player_record)

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        response_dictionary = {
            "player": f"{await my_player_record.get_field(PlayerFields.player_name)}",
            "region": f"{await my_player_record.get_field(PlayerFields.region)}",
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
                    f"You are no longer registered as a player:",
                    f"{response_code_block}",
                    f"This registration has been removed from the League.",
                    f"Please register again if you wish to participate.",
                ]
            ),
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################
        my_player_mention = f"{await discord_helpers.role_mention(guild=interaction.guild, discord_id=await my_player_record.get_field(PlayerFields.discord_id))}"
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"{my_player_mention} has left the League.",
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
