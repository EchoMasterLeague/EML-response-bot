from bot_dialogues import choices
from database.database_full import FullDatabase
from database.enums import InviteStatus, TeamStatus
from database.fields import (
    TeamInviteFields,
    PlayerFields,
    TeamFields,
    TeamPlayerFields,
    SuspensionFields,
)
from utils import discord_helpers, database_helpers, general_helpers
import discord
import constants


async def team_player_accept(
    database: FullDatabase,
    interaction: discord.Interaction,
):
    """Add the requestor to their new Team"""
    try:
        #######################################################################
        #                               RECORDS                               #
        #######################################################################
        # "To" Player
        to_player_records = await database.table_player.get_player_records(
            discord_id=interaction.user.id
        )
        assert to_player_records, f"You are not registered as a player."
        to_player_record = to_player_records[0]
        # "To" Suspensions
        to_suspension_records = await database.table_suspension.get_suspension_records(
            player_id=await to_player_records[0].get_field(PlayerFields.record_id)
        )
        assert (
            not to_suspension_records
        ), f"You are suspended until {await to_suspension_records[0].get_field(SuspensionFields.expires_at)}."
        # "To" Team Player
        to_teamplayer_records = (
            await database.table_team_player.get_team_player_records(
                player_id=await to_player_record.get_field(PlayerFields.record_id)
            )
        )
        assert not to_teamplayer_records, f"You are already on a team."
        # Team Invites
        team_invite_records = await database.table_team_invite.get_team_invite_records(
            to_player_id=await to_player_record.get_field(PlayerFields.record_id)
        )
        assert team_invite_records, f"No invites found."

        #######################################################################
        #                               OPTIONS                               #
        #######################################################################
        # Get Options
        descriptions = {}
        options_dict = {}
        option_number = 0
        for invite in team_invite_records:
            option_number += 1
            invite_id = await invite.get_field(TeamInviteFields.record_id)
            options_dict[invite_id] = f"Accept ({option_number})"
            descriptions[str(option_number)] = {
                "expires_at": f"{await invite.get_field(TeamInviteFields.invite_expires_at)}",
                "from_captain": f"{await invite.get_field(TeamInviteFields.vw_from_player)}({await invite.get_field(TeamInviteFields.from_player_id)})",
                "from_team": f"{await invite.get_field(TeamInviteFields.vw_team)}",
            }
        # Options View
        options_view = choices.QuestionPromptView(
            options_dict=options_dict,
            initial_button_style=discord.ButtonStyle.success,
        )
        # Button: Clear all invites
        options_view.add_item(
            choices.QuestionOptionButton(
                label="Clear all invites",
                style=discord.ButtonStyle.danger,
                custom_id="clearall",
            )
        )
        # Button: Cancel
        options_view.add_item(
            choices.QuestionOptionButton(
                label="Cancel",
                style=discord.ButtonStyle.primary,
                custom_id="cancel",
            )
        )
        # Show Options
        descriptions_block = await discord_helpers.code_block(
            await general_helpers.format_json(descriptions), "json"
        )
        await interaction.response.send_message(
            view=options_view,
            content="\n".join(
                [
                    f"Team Invites:",
                    f"{descriptions_block}",
                    f"Which team invite would you like to accept?",
                ]
            ),
            ephemeral=True,
        )

        #######################################################################
        #                               CHOICE                                #
        #######################################################################
        # Wait for Choice
        await options_view.wait()
        # Get Choice
        choice = options_view.value
        # Choice: Cancel (default)
        if not choice or choice == "cancel":
            return await discord_helpers.final_message(
                interaction=interaction, message=f"No team selected."
            )
        # Choice: Clear all invites
        if choice == "clearall":
            for invite in team_invite_records:
                await invite.set_field(
                    TeamInviteFields.invite_status, InviteStatus.DECLINED
                )
                await database.table_team_invite.update_team_invite_record(invite)
                await database.table_team_invite.delete_team_invite_record(invite)
            return await discord_helpers.final_message(
                interaction=interaction, message=f"Team Invites cleared."
            )
        # Choice: Accept (#)
        selected_invite = None
        for invite in team_invite_records:
            if choice == await invite.get_field(TeamInviteFields.record_id):
                selected_invite = invite
                break
        assert selected_invite, f"Team Invite not found."

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################

        # Update Team Invite
        await selected_invite.set_field(
            TeamInviteFields.invite_status, InviteStatus.ACCEPTED
        )
        from_player_id = await selected_invite.get_field(
            TeamInviteFields.from_player_id
        )
        to_player_id = await selected_invite.get_field(TeamInviteFields.to_player_id)
        assert from_player_id != to_player_id, f"Cannot accept your own invites."
        await database.table_team_invite.update_team_invite_record(selected_invite)

        # "From" Team
        from_team_records = await database.table_team.get_team_records(
            record_id=await selected_invite.get_field(TeamInviteFields.from_team_id)
        )
        assert from_team_records, f"Team not found."
        from_team_record = from_team_records[0]

        # "From" TeamPlayers
        from_teamplayer_records = (
            await database.table_team_player.get_team_player_records(
                team_id=await from_team_record.get_field(TeamFields.record_id)
            )
        )
        assert from_teamplayer_records, f"Team was disbanded"
        assert (
            len(from_teamplayer_records) + 1 <= constants.TEAM_PLAYERS_MAX
        ), f"Team already has the maximum number of players ({constants.TEAM_PLAYERS_MAX})."

        # Add "To" Player to Team
        new_teamplayer_record = (
            await database.table_team_player.create_team_player_record(
                team_id=await from_team_record.get_field(TeamFields.record_id),
                team_name=await from_team_record.get_field(TeamFields.team_name),
                player_id=await to_player_record.get_field(PlayerFields.record_id),
                player_name=await to_player_record.get_field(PlayerFields.player_name),
            )
        )
        assert new_teamplayer_record, f"Error: Failed to add player to team."
        from_teamplayer_records.append(new_teamplayer_record)

        # Update "To" Discord Roles
        await discord_helpers.add_member_to_team(
            member=interaction.user,
            team_name=await new_teamplayer_record.get_field(TeamPlayerFields.vw_team),
        )

        # Update "From" Team Active Status
        if len(from_teamplayer_records) >= constants.TEAM_PLAYERS_MIN:
            await from_team_record.set_field(TeamFields.status, TeamStatus.ACTIVE)
            await database.table_team.update_team_record(from_team_record)

        # Update roster view
        await database_helpers.update_roster_view(
            database=database,
            team_id=await new_teamplayer_record.get_field(TeamPlayerFields.team_id),
        )

        # Delete Team Invites
        for intive in team_invite_records:
            invite_id = await intive.get_field(TeamInviteFields.record_id)
            selected_id = await selected_invite.get_field(TeamInviteFields.record_id)
            if invite_id != selected_id:
                await database.table_team_invite.delete_team_invite_record(intive)
        await database.table_team_invite.delete_team_invite_record(selected_invite)

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        team_name = f"{await new_teamplayer_record.get_field(TeamPlayerFields.vw_team)}"
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
            "team_name": f"{await new_teamplayer_record.get_field(TeamPlayerFields.vw_team)}",
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
                    f"You have joined Team `{team_name}`.",
                    f"{response_code_block}",
                ]
            ),
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################
        to_player_mention = f"{await discord_helpers.role_mention(guild=interaction.guild, discord_id=await new_teamplayer_record.get_field(TeamPlayerFields.player_id))}"
        team_mention = f"{await discord_helpers.role_mention(guild=interaction.guild, team_name=await new_teamplayer_record.get_field(TeamPlayerFields.vw_team))}"
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"{to_player_mention} has joined {team_mention}",
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
