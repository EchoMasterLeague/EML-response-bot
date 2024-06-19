from database.database_full import FullDatabase
from database.fields import PlayerFields, TeamPlayerFields, TeamFields
from database.records import PlayerRecord
from utils import discord_helpers, database_helpers, general_helpers
import discord
import logging

logger = logging.getLogger(__name__)


async def team_disband(
    database: FullDatabase,
    interaction: discord.Interaction,
):
    """Disband the requestor's Team"""
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
        my_player = my_player_records[0]
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
        # "Our" Player
        our_player_records: list[PlayerRecord] = []
        for teamplayer in our_teamplayer_records:
            player_records = await database.table_player.get_player_records(
                record_id=await teamplayer.get_field(TeamPlayerFields.player_id)
            )
            assert player_records, f"Teammate not found."
            our_player_records.append(player_records[0])
        assert our_player_records, f"Teammates not found."
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

        # Remove Discord roles
        for player in our_player_records:
            member = await discord_helpers.member_from_discord_id(
                guild=interaction.guild,
                discord_id=await player.get_field(PlayerFields.discord_id),
            )
            await discord_helpers.member_remove_team_roles(member)
        await discord_helpers.guild_remove_team_role(
            guild=interaction.guild,
            team_name=await our_team.get_field(TeamFields.team_name),
        )

        # Delete "Our" TeamPlayer
        for teamplayer in our_teamplayer_records:
            # Create Cooldown
            new_cooldown_record = await database.table_cooldown.create_cooldown_record(
                player_id=await teamplayer.get_field(TeamPlayerFields.player_id),
                old_team_id=await teamplayer.get_field(TeamPlayerFields.team_id),
                player_name=await teamplayer.get_field(TeamPlayerFields.vw_player),
                old_team_name=await our_team.get_field(TeamFields.team_name),
            )
            assert new_cooldown_record, "Error: Failed to create cooldowns."
            # Delete TeamPlayer
            await database.table_team_player.delete_team_player_record(teamplayer)

        # Delete "Our" Team
        await database.table_team.delete_team_record(our_team)

        # Update roster view
        await database_helpers.update_roster_view(
            database=database, team_id=await our_team.get_field(TeamFields.record_id)
        )

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        team_name = f"{await our_team.get_field(TeamFields.team_name)}"
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
                    f"Team `{team_name}` has been disbanded.",
                    f"Data removed:",
                    f"{response_code_block}",
                ]
            ),
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################
        team_name = await our_team.get_field(TeamFields.team_name)
        my_player_mention = f"{await discord_helpers.role_mention(guild=interaction.guild, discord_id=await my_player.get_field(PlayerFields.discord_id))}"
        player_mentions = []
        for player in our_player_records:
            my_id = await my_player.get_field(PlayerFields.record_id)
            if my_id != await player.get_field(PlayerFields.discord_id):
                player_mention = f"{await discord_helpers.role_mention(guild=interaction.guild, discord_id=await player.get_field(PlayerFields.discord_id))}"
                player_mentions.append(player_mention)
        player_mentions = ", ".join(player_mentions)
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"`{team_name}` has been disbanded by {my_player_mention}, removing [{player_mentions}]",
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.fail_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
