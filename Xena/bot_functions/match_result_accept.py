from database.fields import (
    MatchFields,
    MatchResultInviteFields as ResultFields,
    PlayerFields,
    TeamFields,
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

        # Get Options
        match_result_offers = {}
        options_dict = {}
        option_number = 0
        for invite in match_result_invites:
            option_number += 1
            invite_id = await invite.get_field(ResultFields.record_id)
            options_dict[invite_id] = f"Accept ({option_number})"
            match_result_offers[str(option_number)] = {
                "invite_id": invite_id,
                "created_at": f"{await invite.get_field(ResultFields.created_at)}",
                "expires_at": f"{await invite.get_field(ResultFields.invite_expires_at)}",
                "match_type": f"{await invite.get_field(ResultFields.match_type)}",
                "opposing_team": f"{await invite.get_field(ResultFields.vw_from_team)}",
                "your_outcome": f"{await match_helpers.get_reversed_outcome(await invite.get_field(ResultFields.match_outcome))}",
                "scores": await match_helpers.get_scores_display_dict(
                    await match_helpers.get_reversed_scores(await invite.get_scores())
                ),
            }
        # Options View
        view = choices.QuestionPromptView(
            options_dict=options_dict,
            initial_button_style=discord.ButtonStyle.success,
        )
        # Button: Clear all invites
        view.add_item(
            choices.QuestionOptionButton(
                label="Clear all invites",
                style=discord.ButtonStyle.danger,
                custom_id="clearall",
            )
        )
        # Button: Cancel
        view.add_item(
            choices.QuestionOptionButton(
                label="Cancel",
                style=discord.ButtonStyle.primary,
                custom_id="cancel",
            )
        )
        # Show Options
        match_result_offers_block = await discord_helpers.code_block(
            await general_helpers.format_json(match_result_offers), "json"
        )
        await interaction.response.send_message(
            content=f"Match Result Invites:\n{match_result_offers_block}\n\nWarning: Once accepted, this cannot be undone.",
            view=view,
            ephemeral=True,
        )

        ############################
        #        CHOICE            #
        ############################
        # Wait for Choice
        await view.wait()
        # Get Choice
        choice = view.value
        if not choice or choice == "cancel":
            return await discord_helpers.final_message(
                interaction, message=f"No match result selected."
            )
        # Choice: Clear all invites
        if choice == "clearall":
            for invite in match_result_invites:
                await database.table_match_result_invite.delete_match_result_invite_record(
                    invite
                )
            message = "Match Result Invites cleared."
            return await discord_helpers.final_message(interaction, message)
        # Choice: Accept (#)
        selected_invite = None
        for invite in match_result_invites:
            invite_id = await invite.get_field(ResultFields.record_id)
            if invite_id == choice:
                selected_invite = invite
                break
        assert selected_invite, f"Match Result Invite not found."

        ############################
        #        PROCESSING        #
        ############################

        # Get details from the selected invite record
        from_team_id = await selected_invite.get_field(ResultFields.from_team_id)
        to_team_id = await selected_invite.get_field(ResultFields.to_team_id)
        outcome = await selected_invite.get_field(ResultFields.match_outcome)
        scores = await selected_invite.get_scores()
        # Get details from the associated match record
        match_id = await selected_invite.get_field(ResultFields.match_id)
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
        await selected_invite.set_field(ResultFields.to_player_id, invitee_player_id)
        await selected_invite.set_field(
            ResultFields.invite_status, InviteStatus.ACCEPTED
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

        response_outcomes = {
            MatchResult.WIN: "team_a",
            MatchResult.LOSS: "team_b",
            MatchResult.DRAW: "draw",
        }
        response_dictionary = {
            "results_status": "confirmed",
            "match_time_utc": f"{await match_record.get_field(MatchFields.match_timestamp)}",
            "match_time_eml": f"{await match_record.get_field(MatchFields.match_date)} {await match_record.get_field(MatchFields.match_time_et)}",
            "match_type": f"{await match_record.get_field(MatchFields.match_type)}",
            "team_a": f"{await match_record.get_field(MatchFields.vw_team_a)}",
            "team_b": f"{await match_record.get_field(MatchFields.vw_team_b)}",
            "winner": f"{response_outcomes[outcome]}",
            "scores": await match_helpers.get_scores_display_dict(
                await match_record.get_scores()
            ),
        }
        response_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(response_dictionary), "json"
        )
        await discord_helpers.final_message(
            interaction=interaction,
            message=(
                f"Match Result Invite accepted:\n"
                f"{response_code_block}\n"
                f"Match results confirmed."
            ),
        )

        ############################
        #        LOGGING           #
        ############################

        log_outcomes = {
            MatchResult.WIN: "wins against",
            MatchResult.LOSS: "loses to",
            MatchResult.DRAW: "draws with",
        }
        match_type = f"{await match_record.get_field(MatchFields.match_type)}"
        team_a_mention = f"{await discord_helpers.role_mention(guild=interaction.guild,team_name=await match_record.get_field(MatchFields.vw_team_a))}"
        team_b_mention = f"{await discord_helpers.role_mention(guild=interaction.guild,team_name=await match_record.get_field(MatchFields.vw_team_b))}"
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"{team_a_mention} {log_outcomes[outcome]} {team_b_mention} in a `{match_type}` match",
        )
    # Error Handling
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
