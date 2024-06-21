from database.fields import (
    PlayerFields,
    TeamFields,
    MatchFields,
    TeamPlayerFields,
    LeagueSubMatchInviteFields,
)
from database.database_full import FullDatabase
from database.enums import Bool, MatchType, InviteStatus, MatchStatus
from utils import discord_helpers, general_helpers, match_helpers
import constants
import discord
import logging

logger = logging.getLogger(__name__)


async def league_sub_match_invite(
    database: FullDatabase,
    interaction: discord.Interaction,
    sub_player_member: discord.Member,
    our_team_role: discord.Role,
    opponent_team_role: discord.Role,
    match_type: str,
    year: int,
    month: int,
    day: int,
    time: str,
    am_pm: str,
):
    """Send a League Sub Match Invite to a Team"""
    try:
        # this could take a while, so defer the response
        await interaction.response.defer()
        #######################################################################
        #                               RECORDS                               #
        #######################################################################
        # "My" Player
        my_player_records = await database.table_player.get_player_records(
            discord_id=interaction.user.id
        )
        assert my_player_records, f"You are not registered as a player."
        my_player_record = my_player_records[0]
        # "Sub" Player
        sub_player_records = await database.table_player.get_player_records(
            discord_id=sub_player_member.id
        )
        assert sub_player_records, f"Substitute not registered as a player."
        sub_player_record = sub_player_records[0]
        assert await sub_player_record.get_field(
            PlayerFields.is_sub
        ), f"Player not registerd as a League Substitue"
        # "Sub" TeamPlayer
        sub_teamplayer_records = (
            await database.table_team_player.get_team_player_records(
                player_id=await sub_player_record.get_field(PlayerFields.record_id)
            )
        )
        assert not sub_teamplayer_records, f"Substitute is a member of a team."
        # "Our" Team
        our_team_records = await database.table_team.get_team_records(
            team_name=await discord_helpers.get_team_name_from_role(our_team_role)
        )
        assert our_team_records, f"Your team could not be found."
        our_team_record = our_team_records[0]
        # "Our" TeamPlayer
        our_teamplayer_records = (
            await database.table_team_player.get_team_player_records(
                team_id=await our_team_record.get_field(TeamFields.record_id),
            )
        )
        assert our_teamplayer_records, f"Your team has no players."
        my_player_id = await my_player_record.get_field(PlayerFields.record_id)
        sub_player_id = await sub_player_record.get_field(PlayerFields.record_id)
        captain_player_id = None
        cocaptain_player_id = None
        for teamplayer_record in our_teamplayer_records:

            if await teamplayer_record.get_field(TeamPlayerFields.is_captain):
                captain_player_id = await teamplayer_record.get_field(
                    TeamPlayerFields.player_id
                )
                break
            if await teamplayer_record.get_field(TeamPlayerFields.is_co_captain):
                cocaptain_player_id = await teamplayer_record.get_field(
                    TeamPlayerFields.player_id
                )
                break
        print(
            {
                "my_player_id": my_player_id,
                "sub_player_id": sub_player_id,
                "captain_player_id": captain_player_id,
                "cocaptain_player_id": cocaptain_player_id,
                "list": [sub_player_id, captain_player_id, cocaptain_player_id],
                "is_in_list": my_player_id
                and my_player_id
                in [
                    sub_player_id,
                    captain_player_id,
                    cocaptain_player_id,
                ],
            }
        )
        assert my_player_id and my_player_id in [
            sub_player_id,
            captain_player_id,
            cocaptain_player_id,
        ], f"You are not the substitute player, or a team captain"

        # "Their" Team
        opponent_team_name = await discord_helpers.get_team_name_from_role(
            opponent_team_role
        )
        their_team_records = await database.table_team.get_team_records(
            team_name=await discord_helpers.get_team_name_from_role(opponent_team_role)
        )
        assert their_team_records, f"Team `{opponent_team_name}` not found."
        their_team_record = their_team_records[0]
        # Match
        match_type = await match_helpers.get_normalized_match_type(match_type)
        assert (
            match_type
        ), f"Match type must be one of: [{', '.join([str(option.value) for option in MatchType])}]"
        match_epoch = await general_helpers.epoch_from_eml_datetime_strings(
            year=year, month=month, day=day, time=time, am_pm=am_pm
        )
        assert match_epoch, "\n".join(
            [
                f"Year, Month, and Day must be numeric. e.g. year: `1776`, month: `07`, day: `04` for July 4, 1776.",
                f"Time must be in 12-hour format. e.g. `12:00` for ambiguous noon or midnight.",
                f"AM_PM must be `AM` for morning or `PM` for afternoon.",
                f"{constants.TIME_ENTRY_FORMAT_INVALID_ENCOURAGEMENT_MESSAGE}",
            ]
        )
        match_timestamp = await general_helpers.iso_timestamp(match_epoch)
        match_records = await database.table_match.get_match_records(
            match_timestamp=match_timestamp,
            team_a_id=await our_team_record.get_field(TeamFields.record_id),
            team_b_id=await their_team_record.get_field(TeamFields.record_id),
            match_type=match_type,
        )
        match_records += await database.table_match.get_match_records(
            match_timestamp=match_timestamp,
            team_a_id=await their_team_record.get_field(TeamFields.record_id),
            team_b_id=await our_team_record.get_field(TeamFields.record_id),
            match_type=match_type,
        )
        our_team_name = await our_team_record.get_field(TeamFields.team_name)
        their_team_name = await their_team_record.get_field(TeamFields.team_name)
        assert (
            match_records
        ), f"No match of type `{match_type}` scheduled between `{our_team_name}` and `{their_team_name}` at `{match_timestamp}`."
        assert (
            len(match_records) == 1
        ), f"Multiple matches found. Please contact an admin."
        match_record = match_records[0]

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################
        # Existing League Sub Match Invites
        existing_match_invites = await database.table_league_sub_match_invite.get_league_sub_match_invite_records(
            match_id=await match_record.get_field(MatchFields.record_id),
            sub_player_id=await sub_player_record.get_field(PlayerFields.record_id),
            team_id=await our_team_record.get_field(TeamFields.record_id),
            invite_status=InviteStatus.PENDING,
        )
        assert (
            not existing_match_invites
        ), f"LeagueSubMatchInvite for `{sub_player_record.get_field(PlayerFields.player_name)}` playing for `{our_team_record.get_field(TeamFields.team_name)}` already exists"

        # Create League Sub Match Invite
        captain_player_id = None
        vw_captain = None
        for teamplayer_record in our_teamplayer_records:
            my_player_id = await my_player_record.get_field(PlayerFields.record_id)
            this_player_id = await teamplayer_record.get_field(
                TeamPlayerFields.player_id
            )
            is_captain = await teamplayer_record.get_field(TeamPlayerFields.is_captain)
            is_co_captain = await teamplayer_record.get_field(
                TeamPlayerFields.is_co_captain
            )
            if my_player_id == this_player_id and (is_captain or is_co_captain):
                captain_player_id = my_player_id
                vw_captain = await my_player_record.get_field(PlayerFields.player_name)
                break
        new_league_sub_match_invite = await database.table_league_sub_match_invite.create_league_sub_match_invite_record(
            match_id=await match_record.get_field(MatchFields.record_id),
            vw_team=await our_team_record.get_field(TeamFields.team_name),
            team_id=await our_team_record.get_field(TeamFields.record_id),
            vw_sub=await sub_player_record.get_field(PlayerFields.player_name),
            sub_player_id=await sub_player_record.get_field(PlayerFields.record_id),
            vw_captain=vw_captain,
            captain_player_id=captain_player_id,
        )
        assert (
            new_league_sub_match_invite
        ), f"Error: Failed to create league sub match invite."

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        to_mention = f"{await discord_helpers.role_mention(guild=interaction.guild,team_name=await our_team_record.get_field(TeamFields.team_name))}"
        by_mention = f"{await discord_helpers.role_mention(guild=interaction.guild,discord_id=await sub_player_record.get_field(PlayerFields.discord_id))}"
        my_player_id = await my_player_record.get_field(PlayerFields.record_id)
        sub_player_id = await sub_player_record.get_field(PlayerFields.record_id)
        if my_player_id != sub_player_id:
            by_mention, to_mention = to_mention, by_mention
        response_dictionary = {
            "league_sub_match_status": "declared",
            "inivation_expires_at": f"{await new_league_sub_match_invite.get_field(LeagueSubMatchInviteFields.invite_expires_at)}",
            "match_time_utc": f"{await match_record.get_field(MatchFields.match_timestamp)}",
            "match_time_eml": f"{await match_record.get_field(MatchFields.match_date)} {await match_record.get_field(MatchFields.match_time_et)}",
            "match_type": f"{await match_record.get_field(MatchFields.match_type)}",
            "team_a": f"{await match_record.get_field(MatchFields.vw_team_a)}",
            "team_b": f"{await match_record.get_field(MatchFields.vw_team_b)}",
            "sub_team": f"{await new_league_sub_match_invite.get_field(LeagueSubMatchInviteFields.vw_team)}",
            "sub_player": f"{await new_league_sub_match_invite.get_field(LeagueSubMatchInviteFields.vw_sub)}",
        }
        response_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(response_dictionary), "json"
        )
        await discord_helpers.final_message(
            interaction=interaction,
            message="\n".join(
                [
                    f"League Sub Match Declaration sent to {to_mention}:",
                    f"{response_code_block}",
                    f"Waiting on {by_mention} to confirm.",
                ]
            ),
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################
        to_mention = f"{await discord_helpers.role_mention(guild=interaction.guild,team_name=await our_team_record.get_field(TeamFields.team_name))}"
        by_mention = f"{await discord_helpers.role_mention(guild=interaction.guild,discord_id=await sub_player_record.get_field(PlayerFields.discord_id))}"
        my_player_id = await my_player_record.get_field(PlayerFields.record_id)
        sub_player_id = await sub_player_record.get_field(PlayerFields.record_id)
        if my_player_id != sub_player_id:
            by_mention, to_mention = to_mention, by_mention
        eml_date = f"{await match_record.get_field(MatchFields.match_date)}"
        eml_time = f"{await match_record.get_field(MatchFields.match_time_et)}"
        match_timestamp = f"{await match_record.get_field(MatchFields.match_timestamp)}"
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"Leauge Sub Match Declaration sent from {by_mention} to {to_mention} for a match played on `{eml_date}` at `{eml_time}` ET `({match_timestamp})`.",
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.fail_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
