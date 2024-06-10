from database.fields import (
    PlayerFields,
    TeamFields,
    TeamPlayerFields,
    MatchInviteFields,
    MatchFields,
)
from bot_dialogues import choices
from database.database_full import FullDatabase
from database.enums import InviteStatus
from utils import discord_helpers, general_helpers
import discord


async def match_accept(
    database: FullDatabase,
    interaction: discord.Interaction,
):
    """Accept a match invite"""
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
        # "To" TeamPlayer
        to_teamplayer_records = (
            await database.table_team_player.get_team_player_records(
                player_id=await to_player_record.get_field(PlayerFields.record_id)
            )
        )
        assert to_teamplayer_records, f"You are not a member of a team."
        to_teamplayer_record = to_teamplayer_records[0]
        assert await to_teamplayer_record.get_field(
            TeamPlayerFields.is_captain
        ) or await to_teamplayer_record.get_field(
            TeamPlayerFields.is_co_captain
        ), f"You are not a captain."
        # "To" Team
        to_team_records = await database.table_team.get_team_records(
            record_id=await to_teamplayer_record.get_field(TeamPlayerFields.team_id)
        )
        assert to_team_records, f"Your team could not be found."
        to_team_record = to_team_records[0]
        # Match Invites
        match_invite_records = (
            await database.table_match_invite.get_match_invite_records(
                to_team_id=await to_team_record.get_field(TeamFields.record_id)
            )
        )
        assert (
            match_invite_records
        ), f"No match proposals found. You may want to create one to play another team."

        #######################################################################
        #                               OPTIONS                               #
        #######################################################################
        # Get Options
        descriptions = {}
        options_dict = {}
        option_number = 0
        for invite in match_invite_records:
            option_number += 1
            invite_id = await invite.get_field(MatchInviteFields.record_id)
            options_dict[invite_id] = f"Accept ({option_number})"
            descriptions[str(option_number)] = {
                "expires_at": f"{await invite.get_field(MatchInviteFields.invite_expires_at)}",
                "match_type": f"{await invite.get_field(MatchInviteFields.match_type)}",
                "opposing_team": f"{await invite.get_field(MatchInviteFields.vw_from_team)}",
                "game_time_utc": f"{await invite.get_field(MatchInviteFields.match_timestamp)}",
                "game_time_eml": f"{await invite.get_field(MatchInviteFields.match_date)} {await invite.get_field(MatchInviteFields.match_time_et)}",
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
                    f"Match Invites:",
                    f"{descriptions_block}",
                    f"Note: All times in United States Eastern Time (ET).",
                    f"",
                    f"Warning: Once accepted, this cannot be undone.",
                    f"Failure to show at scheduled time will result in automatic forfeiture.",
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
                interaction=interaction, message=f"No match selected."
            )
        # Choice: Clear all invites
        if choice == "clearall":
            for invite in match_invite_records:
                await invite.set_field(
                    MatchInviteFields.invite_status, InviteStatus.DECLINED
                )
                await database.table_match_invite.update_match_invite_record(invite)
                await database.table_match_invite.delete_match_invite_record(invite)
            return await discord_helpers.final_message(
                interaction=interaction, message=f"Match Invites cleared."
            )
        # Choice: Accept (#)
        selected_invite = None
        for invite in match_invite_records:
            if choice == await invite.get_field(MatchInviteFields.record_id):
                selected_invite = invite
                break
        assert selected_invite, f"Match Invite not found."

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################

        # Update Match Invite
        await selected_invite.set_field(
            MatchInviteFields.invite_status, InviteStatus.ACCEPTED
        )
        await selected_invite.set_field(
            MatchInviteFields.to_player_id,
            await to_player_record.get_field(PlayerFields.record_id),
        )
        from_team_id = await selected_invite.get_field(MatchInviteFields.from_team_id)
        to_team_id = await selected_invite.get_field(MatchInviteFields.to_team_id)
        assert from_team_id != to_team_id, f"Cannot accept your own invites."
        await database.table_match_invite.update_match_invite_record(selected_invite)

        # "From" Team
        from_team_records = await database.table_team.get_team_records(
            record_id=from_team_id
        )
        assert from_team_records, f"Opposing team not found."
        from_team_record = from_team_records[0]

        # Create Match
        new_match_record = await database.table_match.create_match_record(
            team_a_id=await from_team_record.get_field(TeamFields.record_id),
            team_b_id=await to_team_record.get_field(TeamFields.record_id),
            vw_team_a=await from_team_record.get_field(TeamFields.team_name),
            vw_team_b=await to_team_record.get_field(TeamFields.team_name),
            match_type=await selected_invite.get_field(MatchInviteFields.match_type),
            match_epoch=await general_helpers.epoch_timestamp(
                await selected_invite.get_field(MatchInviteFields.match_timestamp)
            ),
        )
        assert new_match_record, f"Error: Failed to create match record."

        # Delete Match Invite
        await database.table_match_invite.delete_match_invite_record(selected_invite)

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        response_dictionary = {
            "match_status": "scheduled",
            "match_time_utc": f"{await new_match_record.get_field(MatchFields.match_timestamp)}",
            "match_time_eml": f"{await new_match_record.get_field(MatchFields.match_date)} {await new_match_record.get_field(MatchFields.match_time_et)}",
            "match_type": f"{await new_match_record.get_field(MatchFields.match_type)}",
            "team_a": f"{await new_match_record.get_field(MatchFields.vw_team_a)}",
            "team_b": f"{await new_match_record.get_field(MatchFields.vw_team_b)}",
        }
        response_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(response_dictionary), "json"
        )
        await discord_helpers.final_message(
            interaction=interaction,
            message="\n".join(
                [
                    f"Match accepted:",
                    f"{response_code_block}",
                    f"Match scheduled.",
                    f"",
                    f"Remember: This cannot be undone. Failure to show will result in automatic forfeiture.",
                ]
            ),
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################
        team_a_mention = f"{await discord_helpers.role_mention(guild=interaction.guild,team_name=await new_match_record.get_field(MatchFields.vw_team_a))}"
        team_b_mention = f"{await discord_helpers.role_mention(guild=interaction.guild,team_name=await new_match_record.get_field(MatchFields.vw_team_b))}"
        match_type = await new_match_record.get_field(MatchFields.match_type)
        eml_date = await new_match_record.get_field(MatchFields.match_date)
        eml_time = await new_match_record.get_field(MatchFields.match_time_et)
        match_timestamp = await new_match_record.get_field(MatchFields.match_timestamp)
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"{team_a_mention} and {team_b_mention} have a `{match_type}` match scheduled for `{eml_date}` at `{eml_time}` ET (`{match_timestamp}`)",
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
