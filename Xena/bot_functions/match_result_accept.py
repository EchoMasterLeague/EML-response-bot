from database.fields import (
    PlayerFields,
    TeamFields,
    MatchResultInviteFields,
    MatchFields,
)
from bot_dialogues import choices
from database.database_full import FullDatabase
from database.enums import MatchResult, MatchStatus, InviteStatus
from database.records import MatchRecord
from utils import discord_helpers, database_helpers, general_helpers, match_helpers
import discord


async def match_result_accept(
    database: FullDatabase,
    interaction: discord.Interaction,
):
    """Accept a Match Result Invite"""
    try:
        # Cannot defer because this is interactive
        # Get invitee player details from discord_id
        invitee_player = await database_helpers.get_player_details_from_discord_id(
            database, interaction.user.id
        )
        invitee_player_id = await invitee_player.get_field(PlayerFields.record_id)
        invitee_player_name = await invitee_player.get_field(PlayerFields.player_name)
        # Get invitee team details from invitee player
        invitee_details: database_helpers.TeamDetailsOfPlayer
        invitee_details = await database_helpers.get_team_details_from_player(
            database, player=invitee_player, assert_any_captain=True
        )
        invitee_team = invitee_details.team
        to_team_id = await invitee_team.get_field(TeamFields.record_id)
        # Get match result invites for invitee team
        match_result_invites = (
            await database.table_match_result_invite.get_match_result_invite_records(
                to_team_id=to_team_id
            )
        )
        assert (
            match_result_invites
        ), f"No match results available to confirm. You may want to create a result offer for another team."

        ############################
        #          OPTIONS         #
        ############################

        # Get Options for the user to select
        match_result_offers = {}
        options_dict = {}
        option_number = 0
        for invite in match_result_invites:
            option_number += 1
            invite_id = await invite.get_field(MatchResultInviteFields.record_id)
            # reverse scores
            scores = await invite.get_scores()
            reversed_scores = await match_helpers.get_reversed_scores(scores)
            scores_dict = match_helpers.get_scores_display_dict(reversed_scores)
            # reverse outcome
            outcome = await invite.get_field(MatchResultInviteFields.match_outcome)
            reversed_outcome = await match_helpers.get_reversed_outcome(outcome)
            # get match type and team name
            match_type = await invite.get_field(MatchResultInviteFields.match_type)
            team_name = await invite.get_field(MatchResultInviteFields.vw_from_team)
            # add to options_dict
            options_dict[invite_id] = f"Accept ({option_number})"
            match_result_offers[str(option_number)] = {
                "invite_id": invite_id,
                "match_type": match_type,
                "team": team_name,
                "outcome": reversed_outcome,
                "scores": scores_dict,
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
        match_result_offers_json = await general_helpers.format_json(
            match_result_offers
        )
        match_result_offers_block = await discord_helpers.code_block(
            match_result_offers_json, "json"
        )
        message = f"Match Result Invites:\n{match_result_offers_block}"
        message += "\n\nWarning: Once accepted, this cannot be undone."
        await interaction.response.send_message(
            content=message, view=view, ephemeral=True
        )

        ############################
        #        CHOICE            #
        ############################

        # Wait for the user to make a choice
        await view.wait()
        # Process the user's choice
        choice = view.value
        if not choice or choice == "cancel":
            message = "No match result selected."
            return await discord_helpers.final_message(interaction, message)
        # clear invites
        if choice == "clearall":
            for invite in match_result_invites:
                await database.table_match_result_invite.delete_match_result_invite_record(
                    invite
                )
            message = "Match Result Invites cleared."
            return await discord_helpers.final_message(interaction, message)
        # Get the selected match result invite
        selected_invite = None
        for match_result_invite in match_result_invites:
            invite_id = await match_result_invite.get_field(
                MatchResultInviteFields.record_id
            )
            if invite_id == choice:
                selected_invite = match_result_invite
                break
        assert selected_invite, f"Match Result Invite not found."

        ############################
        #        PROCESSING        #
        ############################

        # Get details from the selected invite record
        from_team_id = await selected_invite.get_field(
            MatchResultInviteFields.from_team_id
        )
        to_team_id = await selected_invite.get_field(MatchResultInviteFields.to_team_id)
        outcome = await selected_invite.get_field(MatchResultInviteFields.match_outcome)
        scores = await selected_invite.get_scores()
        # Get details from the associated match record
        match_id = await selected_invite.get_field(MatchResultInviteFields.match_id)
        match_records = await database.table_match.get_match_records(record_id=match_id)
        assert match_records, f"Error: Failed to find match record."
        match_record = match_records[0]
        team_a_id = await match_record.get_field(MatchFields.team_a_id)
        team_b_id = await match_record.get_field(MatchFields.team_b_id)
        assert team_a_id != team_b_id, f"Cannot accept scores sent by your own team."
        # reverse scores and oucome if the teams are listed the other way in the match record
        if team_a_id != from_team_id:
            outcome = await match_helpers.get_reversed_outcome(outcome)
            scores = await match_helpers.get_reversed_scores(scores)
        # Update Match Record
        await match_record.set_field(
            MatchFields.match_status, MatchStatus.COMPLETED.value
        )
        await match_record.set_scores(scores)
        await match_record.set_field(MatchFields.outcome, outcome)
        match_record = MatchRecord(await match_record.to_list())  # normalize
        await database.table_match.update_match_record(match_record)
        # Update Match Result Invite record
        await selected_invite.set_field(
            MatchResultInviteFields.to_player_id, invitee_player_id
        )
        await selected_invite.set_field(
            MatchResultInviteFields.invite_status, InviteStatus.ACCEPTED
        )
        await database.table_match_result_invite.update_match_result_invite_record(
            selected_invite
        )
        await database.table_match_result_invite.delete_match_result_invite_record(
            selected_invite
        )

        ############################
        #        RESPONSE          #
        ############################

        winner = "draw"
        winner = "team_a" if outcome == MatchResult.WIN else winner
        winner = "team_b" if outcome == MatchResult.LOSS else winner
        time_eml = (
            await match_record.get_field(MatchFields.match_date)
            + " "
            + await match_record.get_field(MatchFields.match_time_et)
        )
        match_dict = {
            "match_played_utc": await match_record.get_field(
                MatchFields.match_timestamp
            ),
            "match_played_eml": time_eml,
            "match_type": await match_record.get_field(MatchFields.match_type),
            "team_a": await match_record.get_field(MatchFields.vw_team_a),
            "team_b": await match_record.get_field(MatchFields.vw_team_b),
            "winner": winner,
            "scores": await match_helpers.get_scores_display_dict(
                await match_record.get_scores()
            ),
            "match_results_status": "confirmed",
        }
        match_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(match_dict), "json"
        )
        message = f"Match Result Invite accepted.\n{match_code_block}\nMatch results confirmed."
        await discord_helpers.final_message(interaction, message)

        ############################
        #        LOGGING           #
        ############################

        # [@TEAM A] "wins against" or "loses to" [@TEAM B]
        team_a_name = await match_record.get_field(MatchFields.vw_team_a)
        team_b_name = await match_record.get_field(MatchFields.vw_team_b)
        team_a_role = await discord_helpers.get_team_role(
            guild=interaction.guild, team_name=team_a_name
        )
        team_b_role = await discord_helpers.get_team_role(
            guild=interaction.guild, team_name=team_b_name
        )
        outcomes = "draws with"
        outcomes = "wins against" if reversed_outcome == MatchResult.WIN else outcomes
        outcomes = "loses to" if reversed_outcome == MatchResult.LOSS else outcomes
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"{team_a_role.mention} {outcomes} {team_b_role.mention} in a `{match_type}` match",
        )

    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
