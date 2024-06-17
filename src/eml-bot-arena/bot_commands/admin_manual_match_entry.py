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
import constants


async def admin_manual_match_entry(
    database: FullDatabase,
    interaction: discord.Interaction,
    year: int = None,
    month: int = None,
    day: int = None,
    time: str = None,
    am_pm: str = None,
    team_a_id: str = None,
    team_b_id: str = None,
    team_a_name: str = None,
    team_b_name: str = None,
    sub_a_name: str = None,
    sub_b_name: str = None,
    match_id: str = None,
    match_type: str = None,
    match_status: str = None,
    outcome: str = None,
    scores: list[list[int, int]] = None,
):
    """Manually Record a Match Result"""
    try:
        # this could take a while, so defer the response
        await interaction.response.defer()
        #######################################################################
        #                               RECORDS                               #
        #######################################################################
        # "A" Team
        team_a_records = []
        if team_a_name or team_a_id:
            team_a_records = await database.table_team.get_team_records(
                record_id=team_a_id, team_name=team_a_name
            )
        team_a_record = team_a_records[0] if team_a_records else None
        # "B" Team
        team_b_records = []
        if team_b_name or team_b_id:
            team_b_records = await database.table_team.get_team_records(
                record_id=team_b_id, team_name=team_b_name
            )
        team_b_record = team_b_records[0] if team_b_records else None
        # Match
        match_records = []
        if match_id:
            match_records = await database.table_match.get_match_records(
                record_id=match_id
            )
        match_record = match_records[0] if match_records else None
        print(general_helpers.format_json(match_record))

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################
        # Existing values
        match_epoch = None
        if match_record:
            if not match_epoch:
                match_epoch = await general_helpers.epoch_timestamp(
                    iso_timestamp=await match_record.get_field(
                        MatchFields.match_timestamp
                    )
                )
            if not match_id:
                match_id = await match_record.get_field(MatchFields.record_id)
            if not match_type:
                match_type = await match_record.get_field(MatchFields.match_type)
            if not match_status:
                match_status = await match_record.get_field(MatchFields.match_status)
            if not outcome:
                outcome = await match_record.get_field(MatchFields.outcome)
            if not scores:
                scores = await match_record.get_scores()
            if not team_a_id:
                team_a_id = await match_record.get_field(MatchFields.team_a_id)
            if not team_b_id:
                team_b_id = await match_record.get_field(MatchFields.team_b_id)
            if not team_a_name:
                team_a_name = await match_record.get_field(MatchFields.vw_team_a)
            if not team_b_name:
                team_b_name = await match_record.get_field(MatchFields.vw_team_b)
            if not sub_a_name:
                sub_a_name = await match_record.get_field(MatchFields.vw_sub_a)
            if not sub_b_name:
                sub_b_name = await match_record.get_field(MatchFields.vw_sub_b)
        if team_a_record:
            team_a_name = await team_a_record.get_field(TeamFields.team_name)
            team_a_id = await team_a_record.get_field(TeamFields.record_id)
        if team_b_record:
            team_b_name = await team_b_record.get_field(TeamFields.team_name)
            team_b_id = await team_b_record.get_field(TeamFields.record_id)
        # Match - Match Type
        if match_type:
            match_type = await match_helpers.get_normalized_match_type(match_type)
            assert (
                match_type
            ), f"Match type must be one of: [{', '.join([str(option.value) for option in MatchType])}]"
        # Match - Status
        if match_status:
            match_status = await match_helpers.get_normalized_match_status(match_status)
            assert (
                match_status
            ), f"Match status must be one of: [{', '.join([str(option.value) for option in MatchStatus])}]"
        # Match - Outcome
        if outcome:
            outcome = await match_helpers.get_normalized_outcome(outcome)
            assert (
                outcome
            ), f"Outcome must be one of: [{', '.join([str(option.value) for option in MatchResult if option != MatchResult.DRAW])}]"
        # Match - Scores
        if scores:
            is_sores_valid = await match_helpers.is_score_structure_valid(scores)
            assert is_sores_valid, f"Error: Scores could not be parsed."
            print(general_helpers.format_json(scores))
            print(general_helpers.format_json(outcome))
            assert await match_helpers.is_outcome_consistent_with_scores(
                outcome=outcome, scores=scores
            ), f"The scores and outcome do not match."
        # Match - Epoch
        if year or month or day or time or am_pm:
            match_epoch = await general_helpers.epoch_from_eml_datetime_strings(
                year=year, month=month, day=day, time=time, am_pm=am_pm
            )
            assert match_epoch, "\n".join(
                [
                    f"Year, Month, and Day must be numeric. e.g. year: `1776`, month: `07`, day: `04` for July 4, 1776.",
                    f"Time must be in 12-hour format. e.g. `12:00` for ambiguous noon or midnight.",
                    f"AM_PM must be `AM` for morning or `PM` for afternoon.",
                    f"e.g. Noon is `12:00 PM`, Midnight is `12:00 AM`.",
                    f"No time zones are needed because all times are assumed to be in Eastern Time (ET).",
                    f"{constants.TIME_ENTRY_FORMAT_INVALID_ENCOURAGEMENT_MESSAGE}",
                ]
            )
        if not match_epoch:
            # Last second of the current season week
            match_epoch = await general_helpers.upcoming_monday() - 1
        # Update Match
        if match_record:
            await match_record.set_field(
                MatchFields.match_timestamp,
                await general_helpers.iso_timestamp(match_epoch),
            )
            await match_record.set_field(
                MatchFields.match_date, await general_helpers.eml_date(match_epoch)
            )
            await match_record.set_field(
                MatchFields.match_time_et, await general_helpers.eml_time(match_epoch)
            )
            await match_record.set_field(
                MatchFields.match_week, await general_helpers.season_week(match_epoch)
            )
            await match_record.set_field(MatchFields.team_a_id, team_a_id)
            await match_record.set_field(MatchFields.team_b_id, team_b_id)
            await match_record.set_field(MatchFields.vw_team_a, team_a_name)
            await match_record.set_field(MatchFields.vw_team_b, team_b_name)
            await match_record.set_field(MatchFields.vw_sub_a, sub_a_name)
            await match_record.set_field(MatchFields.vw_sub_b, sub_b_name)
            await match_record.set_field(MatchFields.match_type, match_type)
            await match_record.set_field(MatchFields.match_status, match_status)
            await match_record.set_field(MatchFields.outcome, outcome)
            await match_record.set_scores(scores)
            await database.table_match.update_record(match_record)
        # Create Match
        if not match_record:
            match_record = await database.table_match.create_match_record(
                match_epoch=match_epoch,
                team_a_id=team_a_id,
                team_b_id=team_b_id,
                vw_team_a=team_a_name,
                vw_team_b=team_b_name,
                vw_sub_a=sub_a_name,
                vw_sub_b=sub_b_name,
                match_type=match_type,
                match_status=match_status,
                outcome=outcome,
                scores=scores,
            )
            assert match_record, f"Error: Failed to create match record."

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        response_outcomes = {
            MatchResult.WIN: "team_a",
            MatchResult.LOSS: "team_b",
            MatchResult.DRAW: "draw",
        }
        winner = response_outcomes[outcome] if outcome else "pending"
        response_dictionary = {
            "match_status": f"{await match_record.get_field(MatchFields.match_status)}",
            "match_time_utc": f"{await match_record.get_field(MatchFields.match_timestamp)}",
            "match_time_eml": f"{await match_record.get_field(MatchFields.match_date)} {await match_record.get_field(MatchFields.match_time_et)}",
            "match_type": f"{await match_record.get_field(MatchFields.match_type)}",
            "team_a": f"{await match_record.get_field(MatchFields.vw_team_a)}",
            "team_b": f"{await match_record.get_field(MatchFields.vw_team_b)}",
            "winner": winner,
            "scores": await match_helpers.get_scores_display_dict(
                await match_record.get_scores()
            ),
        }
        response_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(response_dictionary), "json"
        )
        await discord_helpers.final_message(
            interaction=interaction,
            message="\n".join(
                [
                    f"Match Results entered manually:",
                    f"{response_code_block}",
                    f"Please verify the format in the spreadsheet",
                ]
            ),
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################
        team_a_mention = await discord_helpers.role_mention(
            guild=interaction.guild,
            team_name=f"{await match_record.get_field(MatchFields.vw_team_a)}",
        )
        team_b_mention = await discord_helpers.role_mention(
            guild=interaction.guild,
            team_name=f"{await match_record.get_field(MatchFields.vw_team_b)}",
        )
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"Match updated for {match_type} match between {team_a_mention} and {team_b_mention}",
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
