from database.database_full import FullDatabase
from database.fields import PlayerFields, TeamPlayerFields, TeamFields
from database.enums import TeamStatus
from utils import discord_helpers, database_helpers, general_helpers
import discord
import constants
import logging

logger = logging.getLogger(__name__)


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
        assert my_teamplayer_records, "You are not a member of a team."
        my_teamplayer_record = my_teamplayer_records[0]
        # "Our" TeamPlayers
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

        # "Our" Players
        our_player_records = []
        for teamplayer_record in our_teamplayer_records:
            palyer_records = await database.table_player.get_player_records(
                record_id=await teamplayer_record.get_field(TeamPlayerFields.player_id)
            )
            our_player_records.extend(palyer_records)
        # "Co-Captain" TeamPlayer
        cocaptain_teamplayer_record = None
        for teamplayer_record in our_teamplayer_records:
            if await teamplayer_record.get_field(TeamPlayerFields.is_co_captain):
                cocaptain_teamplayer_record = teamplayer_record
        # "Co-Captain" Player
        cocaptain_player_record = None
        if cocaptain_teamplayer_record:
            cocaptain_player_records = await database.table_player.get_player_records(
                record_id=await cocaptain_teamplayer_record.get_field(
                    TeamPlayerFields.player_id
                )
            )
            assert cocaptain_player_records, "Error: Could not find co-captain player."
            cocaptain_player_record = cocaptain_player_records[0]
        # "Captain" TeamPlayer
        captain_teamplayer_record = None
        for teamplayer_record in our_teamplayer_records:
            if await teamplayer_record.get_field(TeamPlayerFields.is_captain):
                captain_teamplayer_record = teamplayer_record
        # "Captain" Player
        captain_player_record = None
        if captain_teamplayer_record:
            captain_player_records = await database.table_player.get_player_records(
                record_id=await captain_teamplayer_record.get_field(
                    TeamPlayerFields.player_id
                )
            )
            assert captain_player_records, "Error: Could not find captain player."
            captain_player_record = captain_player_records[0]

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################

        # Remove "My" Discord roles
        member = interaction.user
        await discord_helpers.member_remove_team_roles(member)

        # Create "My" Cooldown record
        new_cooldown = await database.table_cooldown.create_cooldown_record(
            player_id=await my_player_record.get_field(PlayerFields.record_id),
            old_team_id=await our_team_record.get_field(TeamFields.record_id),
            player_name=await my_player_record.get_field(PlayerFields.player_name),
            old_team_name=await our_team_record.get_field(TeamFields.team_name),
        )
        assert new_cooldown, "Error: Could not apply cooldown."

        # If "My" TeamPlayer is Captain
        if await my_teamplayer_record.get_field(TeamPlayerFields.is_captain):
            # Ensure co-captain record
            assert (
                cocaptain_teamplayer_record
            ), "You must promote a co-captain before leaving the team."
            # Promote co-captain to captain - Database
            await cocaptain_teamplayer_record.set_field(
                TeamPlayerFields.is_captain, True
            )
            await cocaptain_teamplayer_record.set_field(
                TeamPlayerFields.is_co_captain, False
            )
            await database.table_team_player.update_team_player_record(
                cocaptain_teamplayer_record
            )
            # Promote co-captain to captain - Discord
            assert cocaptain_player_record, "Error: Could not find co-captain player."
            cocaptain_discord_member = await discord_helpers.member_from_discord_id(
                guild=interaction.guild,
                discord_id=await cocaptain_player_record.get_field(
                    PlayerFields.discord_id
                ),
            )
            await discord_helpers.member_remove_captain_roles(
                member=cocaptain_discord_member
            )
            await discord_helpers.member_add_captain_role(
                member=cocaptain_discord_member,
                region=await cocaptain_player_record.get_field(PlayerFields.region),
            )
            # Promote co-captain to captain - Response
            captain_player_record = cocaptain_player_record
            cocaptain_player_record = None

        # Delete "My" TeamPlayer
        await database.table_team_player.delete_team_player_record(my_teamplayer_record)

        # Update "Our" Team Active Status
        if len(our_teamplayer_records) - 1 < constants.TEAM_PLAYERS_MIN:
            await our_team_record.set_field(TeamFields.status, TeamStatus.INACTIVE)
            await database.table_team.update_record(our_team_record)

        # Update roster view
        await database_helpers.update_roster_view(
            database=database,
            team_id=await our_team_record.get_field(TeamFields.record_id),
        )

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        team_name = f"{await our_team_record.get_field(TeamFields.team_name)}"
        captain = (
            await captain_player_record.get_field(PlayerFields.name)
            if captain_player_record
            else None
        )
        cocaptain = (
            await cocaptain_player_record.get_field(PlayerFields.name)
            if cocaptain_player_record
            else None
        )
        players = []
        for teamplayer_record in our_teamplayer_records:
            my_id = await my_player_record.get_field(PlayerFields.record_id)
            if my_id == await teamplayer_record.get_field(TeamPlayerFields.player_id):
                continue
            if await teamplayer_record.get_field(TeamPlayerFields.is_captain):
                continue
            if await teamplayer_record.get_field(TeamPlayerFields.is_co_captain):
                continue
            else:
                players.append(
                    await teamplayer_record.get_field(TeamPlayerFields.vw_player)
                )
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
                    f"You have left `{team_name}`.",
                    f"{response_code_block}",
                ]
            ),
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################
        my_player_mention = f"{await discord_helpers.role_mention(guild=interaction.guild,discord_id=await my_player_record.get_field(PlayerFields.discord_id))}"
        our_team_mention = f"{await discord_helpers.role_mention(guild=interaction.guild,team_name=await our_team_record.get_field(TeamFields.team_name))}"
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"{my_player_mention} has left {our_team_mention}",
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.fail_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
