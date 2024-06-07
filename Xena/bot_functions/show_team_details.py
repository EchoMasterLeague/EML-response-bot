from database.database_full import FullDatabase
from database.fields import PlayerFields, TeamPlayerFields, TeamFields
from utils import discord_helpers, general_helpers
import discord


async def show_team_details(
    database: FullDatabase, interaction: discord.Interaction, team_name: str = None
):
    """Show Details of a Team"""
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
        # Determine desired team
        team = None
        if not team_name:
            requestor_matches = await database.table_player.get_player_records(
                discord_id=interaction.user.id
            )
            assert (
                requestor_matches
            ), f"You must provide a team name, or be on a team to get team details."
            requestor = requestor_matches[0]
            requestor_id = await requestor.get_field(PlayerFields.record_id)
            team_players = await database.table_team_player.get_team_player_records(
                player_id=requestor_id
            )
            assert team_players, f"No team specified."
            team_player = team_players[0]
            team_id = await team_player.get_field(TeamPlayerFields.team_id)
            teams = await database.table_team.get_team_records(record_id=team_id)
            assert teams, f"Team not found."
            team = teams[0]
        # Get info about the Team
        if not team:
            teams = await database.table_team.get_team_records(team_name=team_name)
            assert teams, f"Team not found."
            team = teams[0]
        assert team, f"Team not found."
        team_name = await team.get_field(TeamFields.team_name)
        team_id = await team.get_field(TeamFields.record_id)
        team_players = await database.table_team_player.get_team_player_records(
            team_id=team_id
        )
        # Get info about the Players
        captain_name = None
        co_captain_name = None
        player_names = []
        for team_player in team_players:
            player_id = await team_player.get_field(TeamPlayerFields.player_id)
            players = await database.table_player.get_player_records(
                record_id=player_id
            )
            assert players, f"Player not found."
            player = players[0]
            player_name = await player.get_field(PlayerFields.player_name)
            player_names.append(player_name)
            if await team_player.get_field(TeamPlayerFields.is_captain):
                captain_name = player_name
            elif await team_player.get_field(TeamPlayerFields.is_co_captain):
                co_captain_name = player_name
        player_names.sort()
        # Format the message
        message_dict = {
            "team": team_name,
            "captain": captain_name,
            "co_captain": co_captain_name,
            "players": player_names,
        }
        message = await general_helpers.format_json(message_dict)
        message = await discord_helpers.code_block(message, language="json")
        return await discord_helpers.final_message(interaction, message)

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
