from database.database_full import FullDatabase
from database.fields import PlayerFields, TeamPlayerFields, TeamFields
from utils import discord_helpers, general_helpers
import discord


async def show_team_details(
    database: FullDatabase, interaction: discord.Interaction, discord_role: discord.Role
):
    """Show Details of a Team"""
    try:
        await interaction.response.defer()
        #######################################################################
        #                               RECORDS                               #
        #######################################################################
        # Team
        team_records = await database.table_team.get_team_records(
            team_name=await discord_helpers.get_team_name_from_role(discord_role)
        )
        assert team_records, f"Team `{discord_role.name}` not found."
        team_record = team_records[0]
        # TeamPlayer
        team_name = await team_record.get_field(TeamFields.team_name)
        teamplayer_records = await database.table_team_player.get_team_player_records(
            team_id=await team_record.get_field(TeamFields.record_id)
        )
        assert teamplayer_records, f"Team `{team_name}` has no players."
        # Player
        team_name = await team_record.get_field(TeamFields.team_name)
        player_records = []
        for teamplayer_record in teamplayer_records:
            player_records += await database.table_player.get_player_records(
                record_id=await teamplayer_record.get_field(TeamPlayerFields.player_id)
            )
        assert player_records, f"Team `{team_name}` has no players."

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################
        # Team Data
        captain = None
        cocaptain = None
        players = []
        for teamplayer_record in teamplayer_records:
            player_name = await teamplayer_record.get_field(TeamPlayerFields.vw_player)
            if await teamplayer_record.get_field(TeamPlayerFields.is_captain):
                captain = player_name
            elif await teamplayer_record.get_field(TeamPlayerFields.is_co_captain):
                cocaptain = player_name
            else:
                players.append(player_name)

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        response_dictionary = {
            "team": f"{await team_record.get_field(TeamFields.team_name)}",
            "captain": captain,
            "co-captain": cocaptain,
            "players": sorted(players),
        }
        response_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(response_dictionary), "json"
        )
        await discord_helpers.final_message(
            interaction=interaction,
            message="\n".join(
                [
                    f"Team Details:\n{response_code_block}",
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
