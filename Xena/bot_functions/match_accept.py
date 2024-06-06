from database.fields import (
    PlayerFields,
    TeamFields,
    MatchInviteFields,
    MatchFields,
)
from bot_dialogues import choices
from database.database_full import FullDatabase
from database.enums import InviteStatus
from utils import discord_helpers, database_helpers, general_helpers
import discord


async def match_accept(
    database: FullDatabase,
    interaction: discord.Interaction,
    match_invite_id: str = None,
):
    """Accept a match invite"""
    try:
        if match_invite_id:
            # this could take a while, so defer the response
            await interaction.response.defer()
        # Get invitee player details from discord_id
        invitee_player = await database_helpers.get_player_details_from_discord_id(
            database, interaction.user.id
        )
        invitee_player_id = await invitee_player.get_field(PlayerFields.record_id)
        # Get invitee team details from invitee player
        invitee_details: database_helpers.TeamDetailsOfPlayer
        invitee_details = await database_helpers.get_team_details_from_player(
            database, player=invitee_player, assert_any_captain=True
        )
        invitee_team = invitee_details.team
        invitee_team_id = await invitee_team.get_field(TeamFields.record_id)
        # Get match invites for invitee team
        match_invites = await database.table_match_invite.get_match_invite_records(
            to_team_id=invitee_team_id
        )
        assert match_invites, f"No invites found."

        ####################
        #     OPTIONS      #
        ####################

        if not match_invite_id:
            # Get Options for the user to select
            match_offers = {}
            options_dict = {}
            option_number = 0
            for invite in match_invites:
                option_number += 1
                invite_id = await invite.get_field(MatchInviteFields.record_id)
                match_type = await invite.get_field(MatchInviteFields.match_type)
                team_name = await invite.get_field(MatchInviteFields.vw_from_team)
                match_date = await invite.get_field(MatchInviteFields.match_date)
                match_time = await invite.get_field(MatchInviteFields.match_time_et)
                options_dict[invite_id] = f"Accept ({option_number})"
                match_offers[str(option_number)] = {
                    "invite_id": invite_id,
                    "match_type": match_type,
                    "team": team_name,
                    "date": match_date,
                    "time_et": match_time,
                }
            # Create the view to display the options
            view = choices.QuestionPromptView(
                options_dict=options_dict,
                initial_button_style=discord.ButtonStyle.success,
            )
            # Add option to clear invites
            clearall_button = choices.QuestionOptionButton(
                label="Clear all invites",
                style=discord.ButtonStyle.danger,
                custom_id="clearall",
            )
            view.add_item(clearall_button)
            # Add option to cancel without making a choice
            cancel_button = choices.QuestionOptionButton(
                label="Cancel",
                style=discord.ButtonStyle.primary,
                custom_id="cancel",
            )
            view.add_item(cancel_button)
            # Send the message with the options
            match_offers_json = await general_helpers.format_json(match_offers)
            match_offers_block = await discord_helpers.code_block(
                match_offers_json, "json"
            )
            message = f"Match Invites:\n{match_offers_block}"
            message += "\nNote: All times in United States Eastern Time (ET)."
            message += "\n\nWarning: Once accepted, this cannot be undone."
            message += "\nFailure to show at scheduled time will result in automatic forfeiture."
            await interaction.response.send_message(
                content=message, view=view, ephemeral=True
            )

            ####################
            #     CHOICE       #
            ####################

            # Wait for the user to make a choice
            await view.wait()
            # Process the user's choice
            choice = view.value
            if not choice or choice == "cancel":
                message = "No match selected."
                return await discord_helpers.final_message(interaction, message)
            # clear invites
            if choice == "clearall":
                for invite in match_invites:
                    await database.table_match_invite.delete_match_invite_record(invite)
                message = "Match Invites cleared."
                return await discord_helpers.final_message(interaction, message)
            # set match_invite_id to the user's choice
            match_invite_id = choice
        # Get the selected match invite
        selected_match_invite = None
        for match_invite in match_invites:
            invite_id = await match_invite.get_field(MatchInviteFields.record_id)
            if invite_id == match_invite_id:
                selected_match_invite = match_invite
                break
        assert selected_match_invite, f"Match Invite not found."

        ########################
        #     PROCESSING       #
        ########################

        # update match invite record
        await selected_match_invite.set_field(
            MatchInviteFields.invite_status, InviteStatus.ACCEPTED
        )
        await selected_match_invite.set_field(
            MatchInviteFields.to_player_id, invitee_player_id
        )
        inviter_team_id = await selected_match_invite.get_field(
            MatchInviteFields.from_team_id
        )
        invitee_team_id = await selected_match_invite.get_field(
            MatchInviteFields.to_team_id
        )
        assert inviter_team_id != invitee_team_id, f"Cannot accept your own invite."
        await database.table_match_invite.update_match_invite_record(
            selected_match_invite
        )
        # get relevant fields from match invite
        inviter_team_id = await selected_match_invite.get_field(
            MatchInviteFields.from_team_id
        )
        match_timestamp = await selected_match_invite.get_field(
            MatchInviteFields.match_timestamp
        )
        match_epoch = await general_helpers.epoch_timestamp(match_timestamp)
        match_type = await selected_match_invite.get_field(MatchInviteFields.match_type)
        # create match record
        inviter_team_id = await selected_match_invite.get_field(
            MatchInviteFields.from_team_id
        )
        inviter_team_matches = await database.table_team.get_team_records(
            record_id=inviter_team_id
        )
        assert inviter_team_matches, f"Team not found."
        inviter_team = inviter_team_matches[0]
        inviter_team_name = await inviter_team.get_field(TeamFields.team_name)
        invitee_team_matches = await database.table_team.get_team_records(
            record_id=invitee_team_id
        )
        assert invitee_team_matches, f"Team not found."
        invitee_team = invitee_team_matches[0]
        invitee_team_name = await invitee_team.get_field(TeamFields.team_name)
        assert inviter_team_id != invitee_team_id, f"Cannot play against your own team."
        new_match = await database.table_match.create_match_record(
            team_a_id=inviter_team_id,
            team_b_id=invitee_team_id,
            match_epoch=match_epoch,
            match_type=match_type,
            vw_team_a=inviter_team_name,
            vw_team_b=invitee_team_name,
        )
        assert new_match, f"Error: Failed to create match record."
        # delete match invite record
        await database.table_match_invite.delete_match_invite_record(
            selected_match_invite
        )

        ####################
        #     RESPONSE     #
        ####################

        fields_to_show = [
            MatchFields.vw_team_a,
            MatchFields.vw_team_b,
            MatchFields.match_date,
            MatchFields.match_time_et,
            MatchFields.match_type,
        ]
        full_new_match_dict = await new_match.to_dict()
        clean_new_match_dict = {}
        for field in fields_to_show:
            clean_new_match_dict[field.name] = full_new_match_dict[field.name]
        match_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(clean_new_match_dict), "json"
        )
        message = f"Match Invite accepted. Match created.\n{match_code_block}"
        message += f"\n\nRemember: This cannot be undone. Failure to show will result in automatic forfeiture."
        await discord_helpers.final_message(interaction, message)

        ####################
        #     LOGGING      #
        ####################

        team_a_role = await discord_helpers.get_team_role(
            guild=interaction.guild, team_name=inviter_team_name
        )
        team_b_role = await discord_helpers.get_team_role(
            guild=interaction.guild, team_name=invitee_team_name
        )
        eml_date = await new_match.get_field(MatchFields.match_date)
        eml_time = await new_match.get_field(MatchFields.match_time_et)
        log_message = f"{team_a_role.mention} and {team_b_role.mention} have a `{match_type}` match scheduled for `{eml_date}` at `{eml_time}` (`{match_timestamp}`)"
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=log_message,
        )
    # handle errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
