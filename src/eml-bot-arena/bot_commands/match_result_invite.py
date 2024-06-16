from database.fields import (
    PlayerFields,
    TeamFields,
    MatchFields,
    TeamPlayerFields,
    MatchResultInviteFields,
)
from database.database_full import FullDatabase
from database.enums import MatchType, MatchResult, MatchStatus
from database.records import MatchResultInviteRecord
from utils import discord_helpers, general_helpers, match_helpers
import discord


async def match_result_invite(
    database: FullDatabase,
    interaction: discord.Interaction,
    to_team_role: discord.Role,
    match_type: str,
    outcome: str,
    scores: list[tuple[int, int]],
):
    """Propose Match Result to another Team"""
    try:
        # this could take a while, so defer the response
        await interaction.response.defer()
        #######################################################################
        #                               RECORDS                               #
        #######################################################################
        # "From" Player
        from_player_records = await database.table_player.get_player_records(
            discord_id=interaction.user.id
        )
        assert from_player_records, f"You are not registered as a player."
        from_player_record = from_player_records[0]
        # "From" TeamPlayer
        from_teamplayer_records = (
            await database.table_team_player.get_team_player_records(
                player_id=await from_player_record.get_field(PlayerFields.record_id)
            )
        )
        assert from_teamplayer_records, f"You are not a member of a team."
        from_team_player_record = from_teamplayer_records[0]
        assert await from_team_player_record.get_field(
            TeamPlayerFields.is_captain
        ) or await from_team_player_record.get_field(
            TeamPlayerFields.is_co_captain
        ), f"Only team captains can do this."
        # "From" Team
        from_team_records = await database.table_team.get_team_records(
            record_id=await from_team_player_record.get_field(TeamPlayerFields.team_id)
        )
        assert from_team_records, f"Your team could not be found."
        from_team_record = from_team_records[0]
        # "To" Team
        to_team_name = await discord_helpers.get_team_name_from_role(to_team_role)
        to_team_records = await database.table_team.get_team_records(
            team_name=await discord_helpers.get_team_name_from_role(to_team_role)
        )
        assert to_team_records, f"Team `{to_team_name}` not found."
        to_team_record = to_team_records[0]
        # Match
        match_type = await match_helpers.get_normalized_match_type(match_type)
        assert (
            match_type
        ), f"Match type must be one of: [{', '.join([str(option.value) for option in MatchType])}]"
        match_records = await database.table_match.get_match_records(
            team_a_id=await from_team_record.get_field(TeamFields.record_id),
            team_b_id=await to_team_record.get_field(TeamFields.record_id),
            match_type=match_type,
            match_status=MatchStatus.PENDING.value,
        )
        match_records += await database.table_match.get_match_records(
            team_a_id=await to_team_record.get_field(TeamFields.record_id),
            team_b_id=await from_team_record.get_field(TeamFields.record_id),
            match_type=match_type,
            match_status=MatchStatus.PENDING.value,
        )
        from_team_name = await from_team_record.get_field(TeamFields.team_name)
        to_team_name = await to_team_record.get_field(TeamFields.team_name)
        assert (
            match_records
        ), f"No pending match found between `{from_team_name}` and `{to_team_name}` of type `{match_type}`."
        match_record = match_records[0]

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################
        # Existing Match Result Invites
        existing_match_result_invite_records = (
            await database.table_match_result_invite.get_match_result_invite_records(
                from_team_id=await from_team_record.get_field(TeamFields.record_id),
                to_team_id=await to_team_record.get_field(TeamFields.record_id),
                match_type=await match_record.get_field(MatchFields.match_type),
            )
        )
        from_team_name = await from_team_record.get_field(TeamFields.team_name)
        to_team_name = await to_team_record.get_field(TeamFields.team_name)
        assert (
            not existing_match_result_invite_records
        ), f"Match results already proposed to team `{to_team_name}` from `{from_team_name}`."

        # Scores
        is_sores_valid = await match_helpers.is_score_structure_valid(scores)
        assert is_sores_valid, f"Error: Scores could not be parsed."
        # Outcome
        outcome = await match_helpers.get_normalized_outcome(outcome)
        assert (
            outcome
        ), f"Outcome must be one of: [{', '.join([str(option.value) for option in MatchResult if option != MatchResult.DRAW])}]"
        assert await match_helpers.is_outcome_consistent_with_scores(
            outcome=outcome, scores=scores
        ), f"The scores and outcome do not match. Please ensure you are entering the data with your team's scores first for each round."
        # Create Match Result Invite
        to_team_id = await to_team_record.get_field(TeamFields.record_id)
        from_team_id = await from_team_record.get_field(TeamFields.record_id)
        assert to_team_id != from_team_id, f"Cannot propose scores to your own team."
        new_result_invite: MatchResultInviteRecord = (
            await database.table_match_result_invite.create_match_result_invite_record(
                scores=scores,
                match_outcome=outcome,
                match_id=await match_record.get_field(MatchFields.record_id),
                match_type=await match_record.get_field(MatchFields.match_type),
                from_team_id=await from_team_record.get_field(TeamFields.record_id),
                from_player_id=f"{await from_player_record.get_field(PlayerFields.record_id)}",
                to_team_id=await to_team_record.get_field(TeamFields.record_id),
                vw_from_team=await from_team_record.get_field(TeamFields.team_name),
                vw_to_team=await to_team_record.get_field(TeamFields.team_name),
                vw_from_player=f"{await from_player_record.get_field(PlayerFields.player_name)}",
            )
        )
        assert new_result_invite, f"Error: Failed to create match result invite."

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        to_team_name = await to_team_record.get_field(TeamFields.team_name)
        response_outcomes = {
            MatchResult.WIN: "my_team",
            MatchResult.LOSS: "to_team",
            MatchResult.DRAW: "draw",
        }
        winner = response_outcomes[outcome]
        response_dictionary = {
            "results_status": "pending confirmation",
            "match_time_utc": f"{await match_record.get_field(MatchFields.match_timestamp)}",
            "match_time_eml": f"{await match_record.get_field(MatchFields.match_date)} {await match_record.get_field(MatchFields.match_time_et)}",
            "match_type": f"{await new_result_invite.get_field(MatchResultInviteFields.match_type)}",
            "my_team": f"{await new_result_invite.get_field(MatchResultInviteFields.vw_from_team)}",
            "to_team": f"{await new_result_invite.get_field(MatchResultInviteFields.vw_to_team)}",
            "winner": winner,
            "scores": await match_helpers.get_scores_display_dict(
                await new_result_invite.get_scores()
            ),
        }
        response_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(response_dictionary), "json"
        )
        await discord_helpers.final_message(
            interaction=interaction,
            message="\n".join(
                [
                    f"Match Result Proposal sent to team `{to_team_name}`.",
                    f"{response_code_block}",
                    f"Your opponent must confirm these results before they are officially recorded.",
                ]
            ),
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################
        to_team_mention = await discord_helpers.role_mention(
            guild=interaction.guild,
            team_name=f"{await new_result_invite.get_field(MatchResultInviteFields.vw_to_team)}",
        )
        from_team_mention = await discord_helpers.role_mention(
            guild=interaction.guild,
            team_name=f"{await new_result_invite.get_field(MatchResultInviteFields.vw_from_team)}",
        )
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"Match Results Proposal sent to {to_team_mention} from {from_team_mention}",
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
