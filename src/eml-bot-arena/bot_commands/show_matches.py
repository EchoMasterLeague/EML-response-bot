from database.database_full import FullDatabase
from database.fields import (
    CooldownFields,
    PlayerFields,
    TeamFields,
    TeamPlayerFields,
    SuspensionFields,
    MatchFields,
)
from database.records import CooldownRecord, TeamRecord
from database.enums import MatchStatus
from utils import discord_helpers, general_helpers
import discord
import logging

logger = logging.getLogger(__name__)


async def show_matches(
    database: FullDatabase,
    interaction: discord.Interaction,
    discord_team_role: discord.Role,
):
    """Show upcoming Matches for a team"""
    try:
        await interaction.response.defer()
        #######################################################################
        #                               RECORDS                               #
        #######################################################################
        # "Selected" Team
        selected_team_name = (
            await discord_helpers.get_team_name_from_role(discord_team_role)
            if discord_team_role
            else None
        )
        selected_team_records = (
            await database.table_team.get_team_records(team_name=selected_team_name)
            if selected_team_name
            else []
        )
        assert selected_team_records, f"Team `{selected_team_name}` not found."
        selected_team_record = selected_team_records[0]
        # Matches
        match_records = await database.table_match.get_match_records(
            team_a_id=await selected_team_record.get_field(TeamFields.record_id),
        )
        match_records += await database.table_match.get_match_records(
            team_b_id=await selected_team_record.get_field(TeamFields.record_id),
        )
        match_records = [
            match_record
            for match_record in match_records
            if await match_record.get_field(MatchFields.match_status)
            == MatchStatus.PENDING
        ]
        # Teams
        team_records: list[TeamRecord] = []
        for match_record in match_records:
            team_records += await database.table_team.get_team_records(
                record_id=await match_record.get_field(MatchFields.team_a_id)
            )
            team_records += await database.table_team.get_team_records(
                record_id=await match_record.get_field(MatchFields.team_b_id)
            )

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################
        match_list = []
        for match_record in match_records:
            opponent_id = f"{await match_record.get_field(MatchFields.team_a_id) if await match_record.get_field(MatchFields.team_b_id) == await selected_team_record.get_field(TeamFields.record_id) else await match_record.get_field(MatchFields.team_b_id)}"
            opponent_vw_name = f"{await match_record.get_field(MatchFields.vw_team_a) if await match_record.get_field(MatchFields.team_b_id) == await selected_team_record.get_field(TeamFields.record_id) else await match_record.get_field(MatchFields.vw_team_b)}"
            opponent_team_records = [
                team_record
                for team_record in team_records
                if await team_record.get_field(TeamFields.record_id) == opponent_id
            ]
            opponent_name = (
                await opponent_team_records[0].get_field(TeamFields.team_name)
                if opponent_team_records
                else opponent_vw_name
            )
            match_list += [
                {
                    "match_time_utc": f"{await match_record.get_field(MatchFields.match_timestamp)}",
                    "match_time_eml": f"{await match_record.get_field(MatchFields.match_date)} {await match_record.get_field(MatchFields.match_time_et)}",
                    "match_type": await match_record.get_field(MatchFields.match_type),
                    "opponent": opponent_name,
                }
            ]
        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        selected_team_name = await selected_team_record.get_field(TeamFields.team_name)
        response_dictionary = sorted(match_list, key=lambda x: x["match_time_utc"])
        response_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(response_dictionary), "json"
        )
        await discord_helpers.final_message(
            interaction=interaction,
            message="\n".join(
                [
                    f"Upcoming Matches for **{selected_team_name}**",
                    f"{response_code_block}",
                ]
            ),
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################

    # Errors
    except AssertionError as message:
        await discord_helpers.fail_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
