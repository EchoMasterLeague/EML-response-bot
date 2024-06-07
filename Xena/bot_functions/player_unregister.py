from database.database_full import FullDatabase
from database.fields import PlayerFields
from utils import discord_helpers, player_helpers
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
        #######################################################################
        #                               OPTIONS                               #
        #######################################################################
        #######################################################################
        #                               CHOICE                                #
        #######################################################################
        #######################################################################
        #                             PROCESSING                              #
        #######################################################################
        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        #######################################################################
        #                               LOGGING                               #
        #######################################################################
        # Get Player info
        discord_id = interaction.user.id
        existing_players = await database.table_player.get_player_records(
            discord_id=discord_id
        )

        assert existing_players, "You are not registered."
        existing_player = existing_players[0]
        existing_player_id = await existing_player.get_field(PlayerFields.record_id)
        existing_team_players = (
            await database.table_team_player.get_team_player_records(
                player_id=existing_player_id
            )
        )
        assert not existing_team_players, "You must leave your team first."
        # Remove Player role
        await player_helpers.member_remove_player_role(interaction.user)
        # Delete Player record
        await database.table_player.delete_player_record(existing_player)
        # Success
        message = f"You are no longer registered as a player"
        await discord_helpers.final_message(interaction, message)
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"{interaction.user.mention} has left the League.",
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
