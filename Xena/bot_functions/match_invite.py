from database.fields import (
    PlayerFields,
    TeamFields,
    MatchInviteFields,
)
from database.database_full import FullDatabase
from database.enums import MatchType
from errors.database_errors import EmlRecordAlreadyExists
from utils import discord_helpers, database_helpers, general_helpers
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
        # Verify match type
        normalized_match_type = None
        for match_option in MatchType:
            if str(match_option.value).casefold() == match_type.casefold():
                normalized_match_type = match_option
                break
        assert (
            normalized_match_type
        ), f"Match type must be one of: [{', '.join([str(option.value) for option in MatchType])}]"
        # Convert "YYYY-MM-DD HH:MM AM/PM" to "YYYY-MM-DD HH:MMAM/PM" (remove the space between the time and the AM/PM, but keep the one between the date and time)
        datetime_array = date_time.split(" ")
        date = datetime_array[0]
        time = "".join(datetime_array[1:])
        date_time = f"{date} {time}"
        # Verify time format (raises ValueError if incorrect format)
        datetime_obj = datetime.datetime.strptime(date_time, "%Y-%m-%d %I:%M%p")
        match_epoch = int(datetime_obj.timestamp())
        # Normalize opposing_team_name
        invitee_team_records = await database.table_team.get_team_records(
            team_name=opposing_team_name
        )
        assert invitee_team_records, f"Team '{opposing_team_name}' not found."
        invitee_team_record = invitee_team_records[0]
        opposing_team_name = await invitee_team_record.get_field(TeamFields.team_name)
        # Get inviter player details from discord_id
        inviter_player = await database_helpers.get_player_details_from_discord_id(
            database, interaction.user.id
        )
        inviter_player_id = await inviter_player.get_field(PlayerFields.record_id)
        # Get inviter team details from inviter player
        inviter_details: database_helpers.TeamDetailsOfPlayer
        inviter_details = await database_helpers.get_team_details_from_player(
            database, player=inviter_player, assert_any_captain=True
        )
        inviter_team = inviter_details.team
        inviter_team_id = await inviter_team.get_field(TeamFields.record_id)
        inviter_team_name = await inviter_team.get_field(TeamFields.team_name)
        # Get invitee team from opposing_team_name
        invitee_team_matches = await database.table_team.get_team_records(
            team_name=opposing_team_name
        )
        assert invitee_team_matches, f"Team '{opposing_team_name}' not found."
        invitee_team = invitee_team_matches[0]
        inviter_player_name = await inviter_player.get_field(PlayerFields.player_name)
        invitee_team_id = await invitee_team.get_field(TeamFields.record_id)
        assert inviter_team_id != invitee_team_id, f"Cannot invite your own team."
        new_match_invite = await database.table_match_invite.create_match_invite_record(
            match_type=normalized_match_type,
            match_epoch=match_epoch,
            from_player_id=inviter_player_id,
            from_team_id=inviter_team_id,
            to_team_id=invitee_team_id,
            vw_from_player=inviter_player_name,
            vw_from_team=inviter_team_name,
            vw_to_team=opposing_team_name,
        )
        assert new_match_invite, f"Error: Failed to create match invite."
        fields_to_show = [
            MatchInviteFields.vw_from_team,
            MatchInviteFields.vw_to_team,
            MatchInviteFields.match_date,
            MatchInviteFields.match_time_et,
            MatchInviteFields.match_type,
            MatchInviteFields.invite_expires_at,
        ]
        full_match_invite_dict = await new_match_invite.to_dict()
        clean_match_invite_dict = {}
        for field in fields_to_show:
            clean_match_invite_dict[field.name] = full_match_invite_dict[field.name]
        match_invite_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(clean_match_invite_dict), "json"
        )
        message = (
            f"Match Invite sent to {opposing_team_name}.\n{match_invite_code_block}"
        )
        await discord_helpers.final_message(interaction, message)
        # Log to Channel
        to_team_name = await new_match_invite.get_field(MatchInviteFields.vw_to_team)
        from_team_name = await new_match_invite.get_field(
            MatchInviteFields.vw_from_team
        )
        to_team_role = await discord_helpers.get_team_role(
            guild=interaction.guild, team_name=to_team_name
        )
        to_team_mention = to_team_role.mention if to_team_role else f"`{to_team_name}`"
        from_team_role = await discord_helpers.get_team_role(
            guild=interaction.guild, team_name=from_team_name
        )
        from_team_mention = (
            from_team_role.mention if from_team_role else f"`{from_team_name}`"
        )
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"Match Invite sent from {from_team_mention} to {to_team_mention}",
        )
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except EmlRecordAlreadyExists as message:
        await discord_helpers.final_message(interaction, message)
    except ValueError as error:
        message = f"Date/Time format is {constants.TIME_ENTRY_FORMAT}. {constants.TIMEZONE_ENCOURAGEMENT_MESSAGE}"
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
