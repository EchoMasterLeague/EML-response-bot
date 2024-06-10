from database.database_full import FullDatabase
from database.fields import PlayerFields, TeamFields, TeamPlayerFields, TeamInviteFields
from utils import discord_helpers, database_helpers, general_helpers
import constants
import discord


async def team_player_invite(
    database: FullDatabase,
    interaction: discord.Interaction,
    discord_member: discord.Member,
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
        # "From" TeamInvite
        from_teaminvite_records = (
            await database.table_team_invite.get_team_invite_records(
                from_team_id=await from_team_record.get_field(TeamFields.record_id)
            )
        )
        assert (
            len(from_teaminvite_records) < constants.TEAM_INVITES_SEND_MAX
        ), "Your team has sent too many pending invites."
        # "My" TeamInvites (sent)
        my_teaminvite_records = (
            await database.table_team_invite.get_team_invite_records(
                from_player_id=await from_player_record.get_field(
                    PlayerFields.record_id
                )
            )
        )
        assert (
            len(my_teaminvite_records) < constants.TEAM_INVITES_SEND_MAX
        ), "You have sent too many pending invites."
        # "To" Player
        to_player_records = await database.table_player.get_player_records(
            discord_id=discord_member.id
        )
        assert (
            to_player_records
        ), f"Player `{discord_member.display_name}` not found. Are they registered?"
        assert (
            len(to_player_records) == 1
        ), "Multiple players found. This should not be possible. Please contact a mod or open a ticket."
        to_player_record = to_player_records[0]
        # "To" TeamInvite
        to_teaminvite_records = (
            await database.table_team_invite.get_team_invite_records(
                to_player_id=await to_player_record.get_field(PlayerFields.record_id)
            )
        )
        assert (
            len(to_teaminvite_records) < constants.TEAM_INVITES_RECEIVE_MAX
        ), f"`{await to_player_record.get_field(PlayerFields.player_name)}` has too many pending invites."
        for to_teaminvite_record in to_teaminvite_records:
            from_team_id = await from_team_record.get_field(TeamFields.record_id)
            to_team_id = await to_teaminvite_record.get_field(
                TeamInviteFields.from_team_id
            )
            assert (
                from_team_id != to_team_id
            ), f"`{await to_player_record.get_field(PlayerFields.player_name)}` has a pending invite from `{await to_teaminvite_record.get_field(TeamInviteFields.vw_team)}`."

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
        to_player_name = await to_player_record.get_field(PlayerFields.player_name)
        captain = None
        cocaptain = None
        players = []
        for from_teamplayer_record in from_teamplayer_records:
            if await from_teamplayer_record.get_field(TeamPlayerFields.is_captain):
                captain = await from_teamplayer_record.get_field(
                    TeamPlayerFields.vw_player
                )
            elif await from_teamplayer_record.get_field(TeamPlayerFields.is_co_captain):
                cocaptain = await from_teamplayer_record.get_field(
                    TeamPlayerFields.vw_player
                )
            else:
                players.append(
                    await from_teamplayer_record.get_field(TeamPlayerFields.vw_player)
                )
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
            message="\n".join(
                [
                    f"Team invite sent to `{to_player_name}`.",
                    f"{response_code_block}",
                    f"They still need to accept the invite to join the team.",
                ]
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
