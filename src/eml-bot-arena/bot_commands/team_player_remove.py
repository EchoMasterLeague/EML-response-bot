from database.database_full import FullDatabase
from database.enums import TeamStatus
from database.fields import PlayerFields, TeamFields, TeamPlayerFields
from database.records import TeamPlayerRecord
from utils import discord_helpers, database_helpers, general_helpers
import constants
import discord
import logging

logger = logging.getLogger(__name__)


async def team_player_remove(
    database: FullDatabase,
    interaction: discord.Interaction,
    discord_member: discord.Member,
):
    """Remove a Player from a Team by name"""
    try:
        await interaction.response.defer()
        #######################################################################
        #                               RECORDS                               #
        #######################################################################
        # "My" Player
        my_player_records = await database.table_player.get_player_records(
            discord_id=interaction.user.id
        )
        assert my_player_records, "You are not registered as a player."
        my_player_record = my_player_records[0]
        # "Our" TeamPlayer
        my_teamplayer_records = (
            await database.table_team_player.get_team_player_records(
                player_id=await my_player_record.get_field(PlayerFields.record_id)
            )
        )
        assert my_teamplayer_records, "You are not a member of a team."
        my_teamplayer_record = my_teamplayer_records[0]
        assert await my_teamplayer_record.get_field(
            TeamPlayerFields.is_captain
        ), f"You are not a captain."
        our_teamplayer_records = (
            await database.table_team_player.get_team_player_records(
                team_id=await my_teamplayer_record.get_field(TeamPlayerFields.team_id)
            )
        )
        assert our_teamplayer_records, "No teammates found."
        # "Our" Team
        our_team_records = await database.table_team.get_team_records(
            record_id=await my_teamplayer_record.get_field(TeamPlayerFields.team_id)
        )
        assert our_team_records, "Your team could not be found."
        our_team_record = our_team_records[0]
        # "Their" Player
        their_player_records = await database.table_player.get_player_records(
            discord_id=discord_member.id
        )
        assert (
            their_player_records
        ), f"Player `{discord_member.display_name}` not found."
        their_player_record = their_player_records[0]
        assert await their_player_record.get_field(
            PlayerFields.record_id
        ) != await my_player_record.get_field(
            PlayerFields.record_id
        ), f"You cannot forcibly remove yourself from the team. Use `/{constants.COMMAND_TEAMLEAVE}` or `/{constants.COMMAND_TEAMDISBAND}` instead."
        # "Their" TeamPlayer
        their_player_name = await their_player_record.get_field(
            PlayerFields.player_name
        )
        their_teamplayer_records: list[TeamPlayerRecord] = []
        for teamplayer in our_teamplayer_records:
            teamplayer_id = await teamplayer.get_field(TeamPlayerFields.player_id)
            their_id = await their_player_record.get_field(PlayerFields.record_id)
            if teamplayer_id == their_id:
                their_teamplayer_records.append(teamplayer)
        assert (
            their_teamplayer_records
        ), f"Player `{their_player_name}` is not on your team."
        their_teamplayer_record = their_teamplayer_records[0]

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################

        # Remove "Their" Discord roles
        their_discord_id = await their_player_record.get_field(PlayerFields.discord_id)
        their_discord_member = await discord_helpers.member_from_discord_id(
            guild=interaction.guild, discord_id=their_discord_id
        )
        await discord_helpers.member_remove_team_roles(their_discord_member)

        # Create "Their" Cooldown
        new_cooldown = await database.table_cooldown.create_cooldown_record(
            player_id=await their_player_record.get_field(PlayerFields.record_id),
            old_team_id=await our_team_record.get_field(TeamFields.record_id),
            player_name=await their_player_record.get_field(PlayerFields.player_name),
            old_team_name=await our_team_record.get_field(TeamFields.team_name),
        )
        assert new_cooldown, "Error: Could not apply cooldown."

        # Delete "Their" TeamPlayer
        await database.table_team_player.delete_team_player_record(
            record=their_teamplayer_record
        )

        # Update "Our" Team Active Status
        if len(our_teamplayer_records) - 1 < constants.TEAM_PLAYERS_MIN:
            await our_team_record.set_field(TeamFields.status, TeamStatus.INACTIVE)
            await database.table_team.update_team_record(record=our_team_record)

        # Update roster view
        await database_helpers.update_roster_view(
            database=database,
            team_id=await our_team_record.get_field(TeamFields.record_id),
        )

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        their_player_name = await their_player_record.get_field(
            PlayerFields.player_name
        )
        our_team_name = f"{await our_team_record.get_field(TeamFields.team_name)}"
        captain = None
        cocaptain = None
        players = []
        for player in our_teamplayer_records:
            their_id = await their_player_record.get_field(PlayerFields.record_id)
            if their_id == await player.get_field(TeamPlayerFields.player_id):
                continue
            elif await player.get_field(TeamPlayerFields.is_captain):
                captain = await player.get_field(TeamPlayerFields.vw_player)
            elif await player.get_field(TeamPlayerFields.is_co_captain):
                cocaptain = await player.get_field(TeamPlayerFields.vw_player)
            else:
                players.append(await player.get_field(TeamPlayerFields.vw_player))
        response_dictionary = {
            "team_name": f"{await our_team_record.get_field(TeamFields.team_name)}",
            "is_active": f"{await our_team_record.get_field(TeamFields.status)}",
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
                    f"Player `{their_player_name}` removed from team `{our_team_name}`.",
                    f"{response_code_block}",
                ]
            ),
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################
        their_player_mention = f"{await discord_helpers.role_mention(guild=interaction.guild,discord_id=await their_player_record.get_field(PlayerFields.discord_id))}"
        our_team_mention = f"{await discord_helpers.role_mention(guild=interaction.guild,team_name=await our_team_record.get_field(TeamFields.team_name))}"
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"{their_player_mention} has been removed from {our_team_mention}",
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.fail_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
