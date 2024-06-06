from database.fields import (
    PlayerFields,
    TeamFields,
    MatchResultInviteFields,
    MatchFields,
)
from database.database_full import FullDatabase
from database.enums import MatchType, MatchResult, MatchStatus
from database.records import MatchRecord, MatchResultInviteRecord
from errors.database_errors import EmlRecordAlreadyExists
from utils import discord_helpers, database_helpers, general_helpers, match_helpers
import discord


async def match_result_invite(
    database: FullDatabase,
    interaction: discord.Interaction,
    opposing_team_name: str,
    scores: list[tuple[int, int]],
    outcome: str,
    match_type: str = MatchType.ASSIGNED.value,
):
    """Propose Match Result to another Team"""
    try:
        # this could take a while, so defer the response
        await interaction.response.defer()
        # constants
        # message_score_format = "Score format: '1a:1b,2a:2b,3a:3b' (you are team a) e.g. '7:5,4:6,6:4' means you won 7-5, lost 4-6, won 6-4"
        message_outcome_mistmatch = "The scores and outcome do not match. Please ensure you are entering the data with your team's scores first for each round."
        message_warning = "Warning: Once accepted, this cannot be undone."
        # Get inviter player details from discord_id
        inviter_player = await database_helpers.get_player_details_from_discord_id(
            database, interaction.user.id
        )
        inviter_player_id = await inviter_player.get_field(PlayerFields.record_id)
        # Get inviter team details from inviter player
        inviter_team_details: database_helpers.TeamDetailsOfPlayer
        inviter_team_details = await database_helpers.get_team_details_from_player(
            database, player=inviter_player, assert_any_captain=True
        )
        inviter_team = inviter_team_details.team
        inviter_team_id = await inviter_team.get_field(TeamFields.record_id)
        inviter_team_name = await inviter_team.get_field(TeamFields.team_name)
        # Get invitee team details from opposing_team_name
        invitee_team_matches = await database.table_team.get_team_records(
            team_name=opposing_team_name
        )
        assert invitee_team_matches, f"Team '{opposing_team_name}' not found."
        invitee_team = invitee_team_matches[0]
        opposing_team_name = await invitee_team.get_field(TeamFields.team_name)
        invitee_team_details = await database_helpers.get_team_details_from_team(
            database, team=invitee_team
        )
        invitee_team_id = await invitee_team.get_field(TeamFields.record_id)
        invitee_team_name = await invitee_team.get_field(TeamFields.team_name)
        # parse outcome
        result: MatchResult = None
        for outcome_option in MatchResult:
            if str(outcome_option.value).casefold() == outcome.casefold():
                result = outcome_option
                break
        if not result:
            if outcome.casefold() in [
                "tie".casefold(),
                "ties".casefold(),
                "tied".casefold(),
                "draw".casefold(),
                "draws".casefold(),
                "drawn".casefold(),
                "equal".casefold(),
            ]:
                result = MatchResult.DRAW
            if outcome.casefold() in [
                "win".casefold(),
                "wins".casefold(),
                "won".casefold(),
                "winner".casefold(),
                "victor".casefold(),
                "victory".casefold(),
                "victorious".casefold(),
            ]:
                result = MatchResult.WIN
            if outcome.casefold() in [
                "lose".casefold(),
                "loses".casefold(),
                "loss".casefold(),
                "lost".casefold(),
                "loser".casefold(),
                "defeat".casefold(),
                "defeated".casefold(),
            ]:
                result = MatchResult.LOSS
        assert_message = f"Outcome must be one of: [{', '.join([str(option.value) for option in MatchResult])}]"
        assert result, assert_message
        # validate outcome against scores
        scores_list = scores
        win = 0
        loss = 0
        for round_scores in scores_list:
            if round_scores[0] is None or round_scores[1] is None:
                continue
            if round_scores[0] > round_scores[1]:
                win += 1
            elif round_scores[0] < round_scores[1]:
                loss += 1
        # assert_message = f"{message_outcome_mistmatch}\n{message_score_format}"
        assert_message = f"{message_outcome_mistmatch}"
        if win > loss:
            assert result == MatchResult.WIN, assert_message
        if win < loss:
            assert result == MatchResult.LOSS, assert_message
        if win == loss:
            assert result == MatchResult.DRAW, assert_message
        # find the relevant match record
        match_record: MatchRecord = None
        invitee_team_id = await invitee_team_details.team.get_field(
            TeamFields.record_id
        )
        matches = await database.table_match.get_match_records(
            team_a_id=inviter_team_id,
            team_b_id=invitee_team_id,
            match_type=match_type,
            match_status=MatchStatus.PENDING.value,
        )
        reverse_matches = await database.table_match.get_match_records(
            team_a_id=invitee_team_id,
            team_b_id=inviter_team_id,
            match_type=match_type,
            match_status=MatchStatus.PENDING.value,
        )
        assert_message = f"No pending match found between `{inviter_team_name}` and `{invitee_team_name}` of type `{match_type}`."
        assert matches or reverse_matches, assert_message
        if matches:
            match_record = matches[0]
        elif reverse_matches:
            match_record = reverse_matches[0]
        assert match_record, f"Error: Failed to find match record."
        assert (
            inviter_team_id != invitee_team_id
        ), f"Cannot propose scores to your own team."
        # create match result invite record
        match_id = await match_record.get_field(MatchFields.record_id)
        match_type = await match_record.get_field(MatchFields.match_type)
        inviter_player_name = await inviter_player.get_field(PlayerFields.player_name)
        new_result_invite: MatchResultInviteRecord = (
            await database.table_match_result_invite.create_match_result_invite_record(
                match_id=match_id,
                match_type=match_type,
                from_team_id=inviter_team_id,
                from_player_id=inviter_player_id,
                to_team_id=invitee_team_id,
                match_outcome=result,
                scores=scores_list,
                vw_from_team=inviter_team_name,
                vw_to_team=opposing_team_name,
                vw_from_player=inviter_player_name,
            )
        )
        assert new_result_invite, f"Error: Failed to create match result invite."

        ########################
        #     RESPONSE         #
        ########################

        # gather details
        winner = "draw"
        winner = "from_team" if result == MatchResult.WIN else winner
        winner = "to_team" if result == MatchResult.LOSS else winner
        time_eml = (
            await match_record.get_field(MatchFields.match_date)
            + " "
            + await match_record.get_field(MatchFields.match_time_et)
        )
        # Dictionary
        response_dictionary = {
            "result_status": "Pending confirmation",
            "match_time_utc": await match_record.get_field(MatchFields.match_timestamp),
            "match_time_eml": time_eml,
            "match_type": await match_record.get_field(MatchFields.match_type),
            "from_team": inviter_team_name,
            "to_team": opposing_team_name,
            "winner": winner,
            "scores": await match_helpers.get_scores_display_dict(
                await new_result_invite.get_scores()
            ),
        }
        # code block
        response_code_block = await discord_helpers.code_block(
            f"{await general_helpers.format_json(response_dictionary)}",
            "json",
        )
        # final message
        await discord_helpers.final_message(
            interaction=interaction,
            message=f"Match Result Proposal sent to team `{opposing_team_name}`.\n{response_code_block}\nYour opponent must confirm these results before they are officially recorded.",
        )

        ##################
        #     LOGGING    #
        ##################

        to_team_mention = await discord_helpers.role_mention(
            guild=interaction.guild,
            team_name=opposing_team_name,
        )
        from_team_mention = await discord_helpers.role_mention(
            guild=interaction.guild,
            team_name=inviter_team_name,
        )
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"Match Results Proposal sent to {to_team_mention} from {from_team_mention}",
        )
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except EmlRecordAlreadyExists as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
