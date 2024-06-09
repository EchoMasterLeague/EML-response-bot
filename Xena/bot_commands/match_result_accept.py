from database.fields import (
    MatchFields,
    MatchResultInviteFields as ResultFields,
    PlayerFields,
    TeamFields,
    TeamPlayerFields,
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
        # Match Result Invites
        match_result_invite_records = (
            await database.table_match_result_invite.get_match_result_invite_records(
                to_team_id=await to_team_record.get_field(TeamFields.record_id)
            )
        )
        assert (
            match_result_invite_records
        ), f"No match results available to confirm, You may want to propose match results for another team to confirm."

        #######################################################################
        #                               OPTIONS                               #
        #######################################################################
        # Get Options
        descriptions = {}
        options_dict = {}
        option_number = 0
        for invite in match_result_invite_records:
            option_number += 1
            invite_id = await invite.get_field(ResultFields.record_id)
            options_dict[invite_id] = f"Accept ({option_number})"
            descriptions[str(option_number)] = {
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
                    f"Match Result Invites:",
                    f"{descriptions_block}",
                    f"Warning: Once accepted, this cannot be undone.",
                ]
            ),
            # ephemeral=True,
        )

        #######################################################################
        #                               CHOICE                                #
        #######################################################################
        # Wait for Choice
        await options_view.wait()
        # Get Choice
        choice = options_view.value
        if not choice or choice == "cancel":
            return await discord_helpers.final_message(
                interaction, message=f"No match results selected."
            )
        # Choice: Clear all invites
        if choice == "clearall":
            for invite in match_result_invite_records:
                await invite.set_field(
                    ResultFields.invite_status, InviteStatus.DECLINED
                )
                await database.table_match_result_invite.update_match_result_invite_record(
                    invite
                )
                await database.table_match_result_invite.delete_match_result_invite_record(
                    invite
                )
            message = "Match Result Invites cleared."
            return await discord_helpers.final_message(interaction, message)
        # Choice: Accept (#)
        selected_invite = None
        for invite in match_result_invite_records:
            invite_id = await invite.get_field(ResultFields.record_id)
            if invite_id == choice:
                selected_invite = invite
                break
        assert selected_invite, f"Match Result Invite not found."

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################

        # Update Match Result Invite
        await selected_invite.set_field(
            ResultFields.invite_status, InviteStatus.ACCEPTED
        )
        await selected_invite.set_field(
            ResultFields.to_player_id,
            await to_player_record.get_field(PlayerFields.record_id),
        )
        from_team_id = await selected_invite.get_field(ResultFields.from_team_id)
        to_team_id = await selected_invite.get_field(ResultFields.to_team_id)
        assert from_team_id != to_team_id, f"Cannot accept your own invites."
        await database.table_match_result_invite.update_match_result_invite_record(
            selected_invite
        )

        # Get Match
        match_records = await database.table_match.get_match_records(
            record_id=await selected_invite.get_field(ResultFields.match_id)
        )
        assert match_records, f"Error: Failed to find match record."
        match_record = match_records[0]

        # Get Scores
        scores = await selected_invite.get_scores()
        outcome = await selected_invite.get_field(ResultFields.match_outcome)
        from_team_id = await selected_invite.get_field(ResultFields.from_team_id)
        team_a_id = await match_record.get_field(MatchFields.team_a_id)
        if team_a_id != from_team_id:
            scores = await match_helpers.get_reversed_scores(scores)
            outcome = await match_helpers.get_reversed_outcome(outcome)

        # Update Match
        await match_record.set_field(MatchFields.match_status, MatchStatus.COMPLETED)
        await match_record.set_scores(scores)
        await match_record.set_field(MatchFields.outcome, outcome)
        match_record = MatchRecord(await match_record.to_list())  # normalize
        await database.table_match.update_match_record(match_record)

        # Delete Match Result Invite
        await database.table_match_result_invite.delete_match_result_invite_record(
            selected_invite
        )

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        response_outcomes = {
            MatchResult.WIN: "team_a",
            MatchResult.LOSS: "team_b",
            MatchResult.DRAW: "draw",
        }
        response_outcome = (
            f"{response_outcomes[await match_record.get_field(MatchFields.outcome)]}"
        )
        response_dictionary = {
            "results_status": "confirmed",
            "match_time_utc": f"{await match_record.get_field(MatchFields.match_timestamp)}",
            "match_time_eml": f"{await match_record.get_field(MatchFields.match_date)} {await match_record.get_field(MatchFields.match_time_et)}",
            "match_type": f"{await match_record.get_field(MatchFields.match_type)}",
            "team_a": f"{await match_record.get_field(MatchFields.vw_team_a)}",
            "team_b": f"{await match_record.get_field(MatchFields.vw_team_b)}",
            "winner": f"{response_outcome}",
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
                f"Match Results accepted:\n"
                f"{response_code_block}\n"
                f"Match results confirmed."
            ),
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################
        log_outcomes = {
            MatchResult.WIN: "wins against",
            MatchResult.LOSS: "loses to",
            MatchResult.DRAW: "draws with",
        }
        log_outcome = (
            f"{log_outcomes[await match_record.get_field(MatchFields.outcome)]}"
        )
        team_a_mention = f"{await discord_helpers.role_mention(guild=interaction.guild,team_name=await match_record.get_field(MatchFields.vw_team_a))}"
        team_b_mention = f"{await discord_helpers.role_mention(guild=interaction.guild,team_name=await match_record.get_field(MatchFields.vw_team_b))}"
        match_type = f"{await match_record.get_field(MatchFields.match_type)}"
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"{team_a_mention} {log_outcome} {team_b_mention} in a `{match_type}` match",
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
