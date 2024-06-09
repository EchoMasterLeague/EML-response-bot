from database.database_full import FullDatabase
from database.fields import CooldownFields, PlayerFields, TeamFields, TeamPlayerFields
from database.records import CooldownRecord
from utils import discord_helpers, general_helpers
import discord


async def show_player_details(
    database: FullDatabase,
    interaction: discord.Interaction,
    player_name: str = None,
    discord_id: str = None,
):
    """Show Details of a Player"""
    try:
        await interaction.response.defer()
        #######################################################################
        #                               RECORDS                               #
        #######################################################################
        # Player
        if not discord_id and not player_name:
            discord_id = interaction.user.id
        players = await database.table_player.get_player_records(
            discord_id=discord_id, player_name=player_name
        )
        assert players, "Player not found."

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################
        player_list = []
        for player in players:
            # Cooldown
            cooldowns = await database.table_cooldown.get_cooldown_records(
                player_id=await player.get_field(PlayerFields.record_id)
            )
            cooldown = cooldowns[0] if cooldowns else None
            cooldown_end = (
                await cooldown.get_field(CooldownFields.expires_at)
                if cooldown
                else None
            )
            # TeamPlayer
            teamplayer_records = (
                await database.table_team_player.get_team_player_records(
                    player_id=await player.get_field(PlayerFields.record_id)
                )
            )
            teamplayer_record = teamplayer_records[0] if teamplayer_records else None
            team_name = None
            team_role = None
            if teamplayer_record:
                team_name = await teamplayer_record.get_field(TeamPlayerFields.vw_team)
                team_role = "member"
                if await teamplayer_record.get_field(TeamPlayerFields.is_co_captain):
                    team_role = "co-captain"
                if await teamplayer_record.get_field(TeamPlayerFields.is_captain):
                    team_role = "captain"
            # Player Data
            player_data = {
                "player": await player.get_field(PlayerFields.player_name),
                "region": await player.get_field(PlayerFields.region),
                "cooldown_end": cooldown_end,
                "team": team_name,
                "team_role": team_role,
            }
            if not cooldown_end:
                player_data.pop("cooldown_end")
            player_list.append(player_data)

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        response_dictionary = player_list[0] if len(player_list) == 1 else player_list
        response_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(response_dictionary), "json"
        )
        await discord_helpers.final_message(
            interaction=interaction,
            message="\n".join(
                [
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
