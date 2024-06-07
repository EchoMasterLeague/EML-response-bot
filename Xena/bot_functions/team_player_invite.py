from database.database_full import FullDatabase
from utils import discord_helpers, database_helpers, general_helpers
from database.fields import PlayerFields, TeamFields, TeamPlayerFields
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
        # Get Player Record for inviter
        inviter_matches = await database.table_player.get_player_records(
            discord_id=interaction.user.id
        )
        assert inviter_matches, f"You must be registered as a player to invite players."
        inviter = inviter_matches[0]
        # check permissions
        inviter_team_players = await database.table_team_player.get_team_player_records(
            player_id=await inviter.get_field(PlayerFields.record_id)
        )
        assert (
            inviter_team_players
        ), f"You must be a player on a team to invite players."
        inviter_team_player = inviter_team_players[0]
        inviter_teams = await database.table_team.get_team_records(
            record_id=await inviter_team_player.get_field(TeamPlayerFields.team_id)
        )
        assert inviter_teams, f"You must be a player on a team to invite players."
        inviter_team = inviter_teams[0]
        team_details = await database_helpers.get_team_details_from_player(
            database, inviter, assert_captain=True
        )
        assert team_details, f"You must be a captain to invite players."
        # Get player record for invitee
        assert player_name or player_discord_id, f"Please specify a player to invite."
        invitee_matches = await database.table_player.get_player_records(
            player_name=player_name, discord_id=player_discord_id
        )
        assert (
            invitee_matches
        ), f"Player not found. Please verify the player is registered."
        assert (
            len(invitee_matches) == 1
        ), f"Multiple players found. Please specify the player's Discord ID (nubmers only) to invite them."
        invitee = invitee_matches[0]
        # Create Invite record
        new_invite = await database_helpers.create_team_invite(
            database, inviter, invitee
        )
        # Success
        new_invite_dict = await new_invite.to_dict()
        new_invite_json = await general_helpers.format_json(new_invite_dict)
        new_invite_block = await discord_helpers.code_block(new_invite_json, "json")
        message = f"Team invite sent.\n{new_invite_block}"
        await discord_helpers.final_message(interaction, message)
        # Log to Channel
        invitee_name = await invitee.get_field(PlayerFields.player_name)
        invitee_discord_id = await invitee.get_field(PlayerFields.discord_id)
        invitee_discord_member = await discord_helpers.member_from_discord_id(
            guild=interaction.guild, discord_id=invitee_discord_id
        )
        inviter_team_name = await inviter_team.get_field(TeamFields.team_name)
        team_role = await discord_helpers.get_team_role(
            guild=interaction.guild,
            team_name=inviter_team_name,
        )
        invitee_mention = (
            invitee_discord_member.mention
            if invitee_discord_member
            else f"`{invitee_name}({invitee_discord_id})`"
        )
        role_mention = team_role.mention if team_role else f"`{inviter_team_name}`"
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"Team invite sent to {invitee_mention} by {interaction.user.mention} for {role_mention}.",
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
