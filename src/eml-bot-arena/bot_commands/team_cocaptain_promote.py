from database.database_full import FullDatabase
from database.fields import PlayerFields, TeamPlayerFields, TeamFields
from database.records import TeamPlayerRecord
from utils import discord_helpers, database_helpers, general_helpers
import discord


async def team_cocaptain_promote(
    database: FullDatabase,
    interaction: discord.Interaction,
    discord_member: discord.Member,
):
    """Promote a Player to Team co-captain"""
    try:
        await interaction.response.defer()
        #######################################################################
        #                               RECORDS                               #
        #######################################################################
        # "My" Player
        my_player_records = await database.table_player.get_player_records(
            discord_id=interaction.user.id
        )
        assert my_player_records, f"You are not registered as a player."
        my_player = my_player_records[0]
        # "Their" Player
        their_player_records = await database.table_player.get_player_records(
            discord_id=discord_member.id
        )
        assert their_player_records, f"Player `{discord_member.display_name}`not found."
        their_player = their_player_records[0]
        # "My" TeamPlayer
        my_teamplayer_records = (
            await database.table_team_player.get_team_player_records(
                player_id=await my_player.get_field(PlayerFields.record_id)
            )
        )
        assert my_teamplayer_records, "You are not a member of a team."
        my_teamplayer = my_teamplayer_records[0]
        assert await my_teamplayer.get_field(
            TeamPlayerFields.is_captain
        ), "You are not a captain."
        # "Our" TeamPlayer
        our_teamplayer_records = (
            await database.table_team_player.get_team_player_records(
                team_id=await my_teamplayer.get_field(TeamPlayerFields.team_id)
            )
        )
        assert our_teamplayer_records, "No teammates found."
        # "Their" TeamPlayer
        their_teamplayer_records: list[TeamPlayerRecord] = []
        for teamplayer in our_teamplayer_records:
            their_id = await their_player.get_field(PlayerFields.record_id)
            if their_id == await teamplayer.get_field(TeamPlayerFields.player_id):
                their_teamplayer_records.append(teamplayer)
        assert their_teamplayer_records, "Player is not your team."
        their_teamplayer = their_teamplayer_records[0]
        assert not await their_teamplayer.get_field(
            TeamPlayerFields.is_co_captain
        ), "Player is already co-captain."
        assert await their_teamplayer.get_field(
            TeamPlayerFields.player_id
        ) != await my_teamplayer.get_field(
            TeamPlayerFields.player_id
        ), "Cannot promote yourself."
        # "Our" Team
        our_team_records = await database.table_team.get_team_records(
            record_id=await my_teamplayer.get_field(TeamPlayerFields.team_id)
        )
        assert our_team_records, "Your team could not be found."
        our_team = our_team_records[0]

        #######################################################################
        #                               OPTIONS                               #
        #######################################################################
        #######################################################################
        #                               CHOICE                                #
        #######################################################################
        #######################################################################
        #                             PROCESSING                              #
        #######################################################################

        # Update "Their" Discord roles
        await discord_helpers.member_remove_captain_roles(
            await discord_helpers.member_from_discord_id(
                guild=interaction.guild,
                discord_id=await their_player.get_field(PlayerFields.discord_id),
            )
        )

        # Update "Their" TeamPlayer record
        await their_teamplayer.set_field(TeamPlayerFields.is_co_captain, True)
        await database.table_team_player.update_team_player_record(their_teamplayer)

        # Update roster view
        await database_helpers.update_roster_view(
            database=database, team_id=await our_team.get_field(TeamFields.record_id)
        )

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        their_player_name = await their_player.get_field(PlayerFields.player_name)
        captain = None
        cocaptain = None
        players = []
        for player in our_teamplayer_records:
            if await player.get_field(TeamPlayerFields.is_captain):
                captain = await player.get_field(TeamPlayerFields.vw_player)
            elif await player.get_field(TeamPlayerFields.is_co_captain):
                cocaptain = await player.get_field(TeamPlayerFields.vw_player)
            else:
                players.append(await player.get_field(TeamPlayerFields.vw_player))
        response_dictionary = {
            "team_name": f"{await our_team.get_field(TeamFields.team_name)}",
            "is_active": f"{await our_team.get_field(TeamFields.status)}",
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
                    f"Player `{their_player_name}` promoted to co-captain:",
                    f"{response_code_block}",
                ]
            ),
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################
        their_player_mention = f"{await discord_helpers.role_mention(guild=interaction.guild, discord_id=await their_player.get_field(PlayerFields.discord_id))}"
        team_mention = f"{await discord_helpers.role_mention(guild=interaction.guild, team_name=await our_team.get_field(TeamFields.team_name))}"
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"{their_player_mention} is now Co-Captain of {team_mention}",
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
