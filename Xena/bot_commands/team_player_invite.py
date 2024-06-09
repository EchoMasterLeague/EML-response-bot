from database.database_full import FullDatabase
from utils import discord_helpers, database_helpers, general_helpers
from database.fields import PlayerFields, TeamFields, TeamPlayerFields, TeamInviteFields
import discord


async def team_player_invite(
    database: FullDatabase,
    interaction: discord.Interaction,
    player_name: str = None,
    player_discord_id: str = None,
):
    """Invite a Player to a Team by name"""
    try:
        await interaction.response.defer()
        #######################################################################
        #                               RECORDS                               #
        #######################################################################
        # "From" Player
        from_player_records = await database.table_player.get_player_records(
            discord_id=interaction.user.id
        )
        assert from_player_records, "You are not registered as a player."
        from_player_record = from_player_records[0]
        # "From" TeamPlayer
        from_teamplayer_records = (
            await database.table_team_player.get_team_player_records(
                player_id=await from_player_record.get_field(PlayerFields.record_id)
            )
        )
        assert from_teamplayer_records, "You are not a member of a team."
        from_teamplayer_record = from_teamplayer_records[0]
        assert await from_teamplayer_record.get_field(
            TeamPlayerFields.is_captain
        ), f"You are not a captain."
        from_teamplayer_records = (
            await database.table_team_player.get_team_player_records(
                team_id=await from_teamplayer_record.get_field(TeamPlayerFields.team_id)
            )
        )
        assert from_teamplayer_records, "No teammates found."
        # "From" Team
        from_team_records = await database.table_team.get_team_records(
            record_id=await from_teamplayer_record.get_field(TeamPlayerFields.team_id)
        )
        assert from_team_records, "Your team could not be found."
        from_team_record = from_team_records[0]
        # "To" Player
        assert player_name or player_discord_id, "Please specify a player to invite."
        to_player_records = await database.table_player.get_player_records(
            player_name=player_name, discord_id=player_discord_id
        )
        assert (
            to_player_records
        ), "Player not found. Please verify the player is registered."
        assert (
            len(to_player_records) == 1
        ), "Multiple players found. Please specify the player's Discord ID (nubmers only) to invite them."
        to_player_record = to_player_records[0]

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################
        # Create Invite record
        new_teaminvite_record = (
            await database.table_team_invite.create_team_invite_record(
                from_team_id=await from_team_record.get_field(TeamFields.record_id),
                from_team_name=await from_team_record.get_field(TeamFields.team_name),
                from_player_id=await from_player_record.get_field(
                    PlayerFields.record_id
                ),
                from_player_name=await from_player_record.get_field(
                    PlayerFields.player_name
                ),
                to_player_id=await to_player_record.get_field(PlayerFields.record_id),
                to_player_name=await to_player_record.get_field(
                    PlayerFields.player_name
                ),
            )
        )
        assert new_teaminvite_record, "Error: Failed to create invite."

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        player_name = await to_player_record.get_field(PlayerFields.player_name)
        captain = None
        cocaptain = None
        players = []
        for player in from_teamplayer_records:
            if await player.get_field(TeamPlayerFields.is_captain):
                captain = await player.get_field(TeamPlayerFields.vw_player)
            elif await player.get_field(TeamPlayerFields.is_co_captain):
                cocaptain = await player.get_field(TeamPlayerFields.vw_player)
            else:
                players.append(await player.get_field(TeamPlayerFields.vw_player))
        response_dictionary = {
            "team_name": f"{await new_teaminvite_record.get_field(TeamInviteFields.vw_team)}",
            "is_active": f"{await from_team_record.get_field(TeamFields.status)}",
            "captain": captain,
            "co-captain": cocaptain,
            "players": sorted(players),
        }
        response_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(response_dictionary), "json"
        )
        await discord_helpers.final_message(
            interaction=interaction,
            message=(
                f"Team invite sent to `{player_name}`.\n{response_code_block}\n"
                f"They still need to accept the invite to join the team."
            ),
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################
        to_player_mention = f"{await discord_helpers.role_mention(guild=interaction.guild, discord_id=await new_teaminvite_record.get_field(TeamInviteFields.to_player_id))}"
        from_player_mention = f"{await discord_helpers.role_mention(guild=interaction.guild, discord_id=await new_teaminvite_record.get_field(TeamInviteFields.from_player_id))}"
        team_mention = f"{await discord_helpers.role_mention(guild=interaction.guild, team_name=await new_teaminvite_record.get_field(TeamInviteFields.vw_team))}"
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"Team invite sent to {to_player_mention} by {from_player_mention} for {team_mention}",
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
