from database.database_full import FullDatabase
from database.fields import PlayerFields
from utils import discord_helpers, player_helpers, general_helpers
import discord


async def league_sub_register(database: FullDatabase, interaction: discord.Interaction):
    """Register as a League Substitute"""
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
        # "My" TeamPlayer
        my_teamplayer_records = (
            await database.table_team_player.get_team_player_records(
                player_id=await my_player_record.get_field(PlayerFields.record_id)
            )
        )
        assert not my_teamplayer_records, "You are a member of a team."

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################

        # Update Player record
        await my_player_record.set_field(PlayerFields.is_sub, True)
        await database.table_player.update_player_record(my_player_record)

        # Add League Substitute role
        await player_helpers.member_add_league_sub_role(interaction.user)

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
                    f"Player `{player_name}` registered as a League Substitue:",
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
            message=f"{my_player_mention} has registered as a League Substitute.",
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
