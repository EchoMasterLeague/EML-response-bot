from database.database_full import FullDatabase
from database.fields import PlayerFields, TeamPlayerFields, TeamFields
from utils import discord_helpers, database_helpers
import discord


async def team_player_leave(
    database: FullDatabase,
    interaction: discord.Interaction,
):
    """Remove the requestor from their Team"""
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
        # Get info about the requestor
        requestor_matches = await database.table_player.get_player_records(
            discord_id=interaction.user.id
        )
        assert requestor_matches, f"You must be registered as a Player to leave a Team."
        requestor = requestor_matches[0]
        requestor_player_id = await requestor.get_field(PlayerFields.record_id)
        requestor_team_players = (
            await database.table_team_player.get_team_player_records(
                player_id=requestor_player_id
            )
        )
        assert requestor_team_players, f"You must be on a team to leave."
        requestor_team_player = requestor_team_players[0]
        requestor_is_captain = await requestor_team_player.get_field(
            TeamPlayerFields.is_captain
        )
        # Get info about the Team
        team_id = await requestor_team_player.get_field(TeamPlayerFields.team_id)
        teams = await database.table_team.get_team_records(record_id=team_id)
        assert teams, f"Team not found."
        team = teams[0]
        team_name = await team.get_field(TeamFields.team_name)
        team_players = await database.table_team_player.get_team_player_records(
            team_id=team_id
        )
        if requestor_is_captain:
            # Get info about the co-captain
            co_captain_team_player = None
            for team_player in team_players:
                if await team_player.get_field(TeamPlayerFields.is_co_captain):
                    co_captain_team_player = team_player
            assert (
                co_captain_team_player
            ), f"Captain must promote a co-captain before leaving."
            # promote the co-captain to captain
            co_cap = co_captain_team_player
            await co_cap.set_field(TeamPlayerFields.is_captain, True)
            await co_cap.set_field(TeamPlayerFields.is_co_captain, False)
            await database.table_team_player.update_team_player_record(co_cap)
        # Apply cooldown
        player_name = await requestor.get_field(PlayerFields.player_name)
        new_cooldown = await database.table_cooldown.create_cooldown_record(
            player_id=requestor_player_id,
            old_team_id=team_id,
            player_name=player_name,
            old_team_name=team_name,
        )
        assert new_cooldown, f"Error: Could not apply cooldown."
        # Remove the Player from the Team
        await database.table_team_player.delete_team_player_record(
            requestor_team_player
        )
        # Update Player's Discord roles
        member = interaction.user
        await discord_helpers.member_remove_team_roles(member)
        # Update roster view
        await database_helpers.update_roster_view(database, team_id)
        # Success
        message = f"You have left Team '{team_name}'"
        await discord_helpers.final_message(interaction, message)
        team_role = await discord_helpers.get_team_role(
            guild=interaction.guild, team_name=team_name
        )
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"{member.mention} has left {team_role.mention}",
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
