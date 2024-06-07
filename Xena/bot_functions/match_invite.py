from database.fields import (
    PlayerFields,
    TeamFields,
    MatchInviteFields,
    TeamPlayerFields,
)
from database.database_full import FullDatabase
from database.enums import MatchType, InviteStatus, MatchStatus
from errors.database_errors import EmlRecordAlreadyExists
from utils import discord_helpers, database_helpers, general_helpers, match_helpers
import constants
import datetime
import discord


async def match_invite(
    database: FullDatabase,
    interaction: discord.Interaction,
    match_type: str,
    opposing_team_name: str,
    date_time: str,
):
    """Send a Match Invite to another Team"""
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
        from_team_player_records = (
            await database.table_team_player.get_team_player_records(
                player_id=await from_player_record.get_field(PlayerFields.record_id)
            )
        )
        assert from_team_player_records, f"You are not a member of a team."
        from_team_player_record = from_team_player_records[0]
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
        to_team_records = await database.table_team.get_team_records(
            team_name=opposing_team_name
        )
        assert to_team_records, f"Team `{opposing_team_name}` not found."
        to_team_record = to_team_records[0]

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################
        # Existing Match Invites
        existing_match_invites = (
            await database.table_match_invite.get_match_invite_records(
                from_team_id=await from_team_record.get_field(TeamFields.record_id),
                to_team_id=await to_team_record.get_field(TeamFields.record_id),
                invite_status=InviteStatus.PENDING,
            )
        )
        from_team_mame = await from_team_record.get_field(TeamFields.team_name)
        to_team_name = await to_team_record.get_field(TeamFields.team_name)
        assert (
            not existing_match_invites
        ), f"Match already proposed from `{from_team_mame}` to play `{to_team_name}`."

        # Match Type
        match_type = await match_helpers.get_normalized_match_type(match_type)
        assert (
            match_type
        ), f"Match type must be one of: [{', '.join([str(option.value) for option in MatchType])}]"

        # Match Epoch
        match_epoch = await general_helpers.epoch_from_eml_datetime_string(date_time)
        assert (
            match_epoch
        ), f"Date/Time format is `{constants.TIME_ENTRY_FORMAT}`.\n{constants.TIMEZONE_ENCOURAGEMENT_MESSAGE}"

        # Existing Matches
        existing_matches = await database.table_match.get_match_records(
            team_a_id=await from_team_record.get_field(TeamFields.record_id),
            team_b_id=await to_team_record.get_field(TeamFields.record_id),
            match_type=match_type,
            match_status=MatchStatus.PENDING,
        )
        assert (
            not existing_matches
        ), f"Match already scheduled between `{from_team_mame}` and `{to_team_name}`."

        # Create Match Invite
        from_team_id = await from_team_record.get_field(TeamFields.record_id)
        to_team_id = await to_team_record.get_field(TeamFields.record_id)
        assert from_team_id != to_team_id, f"Cannot play your own team."
        new_match_invite = await database.table_match_invite.create_match_invite_record(
            match_type=match_type,
            match_epoch=match_epoch,
            from_player_id=await from_player_record.get_field(PlayerFields.record_id),
            from_team_id=await from_team_record.get_field(TeamFields.record_id),
            to_team_id=await to_team_record.get_field(TeamFields.record_id),
            vw_from_player=await from_player_record.get_field(PlayerFields.player_name),
            vw_from_team=await from_team_record.get_field(TeamFields.team_name),
            vw_to_team=await to_team_record.get_field(TeamFields.team_name),
        )
        assert new_match_invite, f"Error: Failed to create match invite."

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        to_team_name = await new_match_invite.get_field(MatchInviteFields.vw_to_team)
        response_dictionary = {
            "match_status": "proposed",
            "inivation_expires_at": f"{await new_match_invite.get_field(MatchInviteFields.invite_expires_at)}",
            "match_time_utc": f"{await new_match_invite.get_field(MatchInviteFields.match_timestamp)}",
            "match_time_eml": f"{await new_match_invite.get_field(MatchInviteFields.match_date)} {await new_match_invite.get_field(MatchInviteFields.match_time_et)}",
            "match_type": f"{await new_match_invite.get_field(MatchInviteFields.match_type)}",
            "team_a": f"{await new_match_invite.get_field(MatchInviteFields.vw_from_team)}",
            "team_b": f"{await new_match_invite.get_field(MatchInviteFields.vw_to_team)}",
        }
        response_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(response_dictionary), "json"
        )
        await discord_helpers.final_message(
            interaction=interaction,
            message=(
                f"Match proposal sent to `{to_team_name}`:\n{response_code_block}\nWaiting on opposing team to accept match date/time.\n\n"
                f"Remember: Once accepted, this cannot be undone. Failure to show will result in automatic forfeiture.",
            ),
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################
        from_team_mention = f"{await discord_helpers.role_mention(guild=interaction.guild,team_name=await new_match_invite.get_field(MatchInviteFields.vw_from_team))}"
        to_team_mention = f"{await discord_helpers.role_mention(guild=interaction.guild,team_name=await new_match_invite.get_field(MatchInviteFields.vw_to_team))}"
        eml_date = await new_match_invite.get_field(MatchInviteFields.match_date)
        eml_time = await new_match_invite.get_field(MatchInviteFields.match_time_et)
        match_timestamp = await new_match_invite.get_field(
            MatchInviteFields.match_timestamp
        )
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"Match Proposal sent from {from_team_mention} to {to_team_mention} to be played on `{eml_date}` at `{eml_time}` ET `({match_timestamp})`.",
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
