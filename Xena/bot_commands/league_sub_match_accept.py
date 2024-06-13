from database.fields import (
    MatchFields,
    PlayerFields,
    TeamFields,
    TeamPlayerFields,
    LeagueSubMatchInviteFields as SubInviteFields,
    LeagueSubMatchFields,
)
from bot_dialogues import choices
from database.database_full import FullDatabase
from database.enums import MatchResult, MatchStatus, InviteStatus
from database.records import MatchRecord
from utils import discord_helpers, database_helpers, general_helpers, match_helpers
import discord


async def league_sub_match_accept(
    database: FullDatabase,
    interaction: discord.Interaction,
    sub_player_member: discord.Member,
    our_team_role: discord.Role,
):
    """Accept a Match Result Invite"""
    try:
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
        assert my_player_id and my_player_id in [
            sub_player_id,
            captain_player_id,
            cocaptain_player_id,
        ], f"You are not the substitute player, or a team captain"
        # League Sub Match Invite
        if my_player_id == sub_player_id:
            league_sub_match_invite_records = await database.table_league_sub_match_invite.get_league_sub_match_invite_records(
                sub_player_id=await sub_player_record.get_field(PlayerFields.record_id)
            )
        else:
            league_sub_match_invite_records = await database.table_league_sub_match_invite.get_league_sub_match_invite_records(
                team_id=await our_team_record.get_field(TeamFields.record_id)
            )
        assert (
            league_sub_match_invite_records
        ), f"No League Sub Match Invites available to confirm."
        # Match
        match_records: list[MatchRecord] = []
        for invite in league_sub_match_invite_records:
            these_match_records = await database.table_match.get_match_records(
                record_id=await invite.get_field(SubInviteFields.match_id)
            )
            match_records.extend(these_match_records)

        #######################################################################
        #                               OPTIONS                               #
        #######################################################################
        # Get Options
        descriptions = {}
        options_dict = {}
        option_number = 0
        for invite in league_sub_match_invite_records:
            option_number += 1
            match_record = None
            for match in match_records:
                match_record_id = await match.get_field(MatchFields.record_id)
                invite_match_id = await invite.get_field(SubInviteFields.match_id)
                if match_record_id == invite_match_id:
                    match_record = match
                    break
            assert match_record, f"Match record not found."
            winner_dict = {
                MatchResult.WIN: "team_a",
                MatchResult.LOSS: "team_b",
                MatchResult.DRAW: "draw",
            }
            invite_id = await invite.get_field(SubInviteFields.record_id)
            options_dict[invite_id] = f"Accept ({option_number})"
            descriptions[str(option_number)] = {
                "expires_at": f"{await invite.get_field(SubInviteFields.invite_expires_at)}",
                "match_time_utc": f"{await match_record.get_field(MatchFields.match_timestamp)}",
                "match_time_eml": f"{await match_record.get_field(MatchFields.match_date)} {await match_record.get_field(MatchFields.match_time_et)}",
                "match_type": f"{await match_record.get_field(MatchFields.match_type)}",
                "team_a": f"{await match_record.get_field(MatchFields.vw_team_a)}",
                "team_b": f"{await match_record.get_field(MatchFields.vw_team_b)}",
                "sub_team": f"{await invite.get_field(SubInviteFields.vw_team)}",
                "sub_player": f"{await invite.get_field(SubInviteFields.vw_sub)}",
                "winner": f"{winner_dict[await match_record.get_field(MatchFields.outcome)] if await match_record.get_field(MatchFields.outcome) else "pending"}",
                "scores": await match_helpers.get_scores_display_dict(
                    await match_record.get_scores()
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
                    f"League Sub Match Invites:",
                    f"{descriptions_block}",
                    f"Warning: Once accepted, this cannot be undone.",
                ]
            ),
            ephemeral=True,
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
            for invite in league_sub_match_invite_records:
                await invite.set_field(
                    SubInviteFields.invite_status, InviteStatus.DECLINED
                )
                await database.table_league_sub_match_invite.update_league_sub_match_invite_record(
                    invite
                )
                await database.table_league_sub_match_invite.delete_league_sub_match_invite_record(
                    invite
                )
            message = "League Sub Match Invites cleared."
            return await discord_helpers.final_message(interaction, message)
        # Choice: Accept (#)
        selected_invite = None
        for invite in league_sub_match_invite_records:
            invite_id = await invite.get_field(SubInviteFields.record_id)
            if invite_id == choice:
                selected_invite = invite
                break
        assert selected_invite, f"League Sub Match Invite not found."

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################

        # Update League Sub Match Invite
        await selected_invite.set_field(
            SubInviteFields.invite_status, InviteStatus.ACCEPTED
        )
        my_player_id = await my_player_record.get_field(PlayerFields.record_id)
        sub_player_id = await sub_player_record.get_field(PlayerFields.record_id)
        if my_player_id != sub_player_id:
            await selected_invite.set_field(
                SubInviteFields.captain_player_id,
                await my_player_record.get_field(PlayerFields.record_id),
            )
            await selected_invite.set_field(
                SubInviteFields.vw_captain,
                await my_player_record.get_field(PlayerFields.player_name),
            )
        await database.table_match_result_invite.update_match_result_invite_record(
            selected_invite
        )

        # Update Match
        match_record = None
        for match in match_records:
            match_record_id = await match.get_field(MatchFields.record_id)
            invite_match_id = await selected_invite.get_field(SubInviteFields.match_id)
            if match_record_id == invite_match_id:
                match_record = match
                break
        assert match_record, f"Match record not found."
        team_a_id = await match_record.get_field(MatchFields.team_a_id)
        team_b_id = await match_record.get_field(MatchFields.team_b_id)
        sub_team_id = await selected_invite.get_field(SubInviteFields.team_id)
        if sub_team_id == team_a_id:
            await match_record.set_field(
                MatchFields.vw_team_a,
                await our_team_record.get_field(TeamFields.team_name),
            )
        if sub_player_id == team_b_id:
            await match_record.set_field(
                MatchFields.vw_team_b,
                await our_team_record.get_field(TeamFields.team_name),
            )
        await database.table_match.update_match_record(match_record)

        # Create League Sub Match
        winner_dict = {
            MatchResult.WIN: "team_a",
            MatchResult.LOSS: "team_b",
            MatchResult.DRAW: "draw",
        }
        new_league_sub_match_record = await database.table_league_sub_match.create_league_sub_match_record(
            match_id=await match_record.get_field(MatchFields.record_id),
            player_id=await sub_player_record.get_field(PlayerFields.record_id),
            team_id=await our_team_record.get_field(TeamFields.record_id),
            vw_player=await sub_player_record.get_field(PlayerFields.player_name),
            vw_team=await our_team_record.get_field(TeamFields.team_name),
            vw_timestamp=await match_record.get_field(MatchFields.match_timestamp),
            vw_type=await match_record.get_field(MatchFields.match_type),
            vw_team_a=await match_record.get_field(MatchFields.vw_team_a),
            vw_team_b=await match_record.get_field(MatchFields.vw_team_b),
            vw_winner=f"{winner_dict[await match_record.get_field(MatchFields.outcome)]}",
        )

        # Delete League Sub Match Invite
        await database.table_league_sub_match_invite.delete_league_sub_match_invite_record(
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
        response_dictionary = {
            "league_sub_match_status": "confirmed",
            "match_time_utc": f"{await new_league_sub_match_record.get_field(LeagueSubMatchFields.vw_timestamp)}",
            "match_time_eml": f"{await match_record.get_field(MatchFields.match_date)} {await match_record.get_field(MatchFields.match_time_et)}",
            "match_type": f"{await new_league_sub_match_record.get_field(LeagueSubMatchFields.vw_type)}",
            "team_a": f"{await new_league_sub_match_record.get_field(LeagueSubMatchFields.vw_team_a)}",
            "team_b": f"{await new_league_sub_match_record.get_field(LeagueSubMatchFields.vw_team_b)}",
            "sub_team": f"{await new_league_sub_match_record.get_field(LeagueSubMatchFields.vw_team)}",
            "sub_player": f"{await new_league_sub_match_record.get_field(LeagueSubMatchFields.vw_player)}",
            "winner": f"{response_outcomes[await match_record.get_field(MatchFields.outcome)]}",
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
                    f"League Sub Match Invite accepted:",
                    f"{response_code_block}",
                    f"League Sub Match confirmed.",
                ]
            ),
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################
        our_team_id = await our_team_record.get_field(TeamFields.record_id)
        team_a_id = await match_record.get_field(MatchFields.team_a_id)
        our_team_mention = f"{await discord_helpers.role_mention(guild=interaction.guild,team_name=await our_team_record.get_field(TeamFields.team_name))}"
        sub_player_mention = f"{await discord_helpers.role_mention(guild=interaction.guild,discord_id=await sub_player_record.get_field(PlayerFields.discord_id))}"
        opponent_team_mention = f"{await discord_helpers.role_mention(guild=interaction.guild,team_name=await match_record.get_field(MatchFields.vw_team_a if our_team_id == team_a_id else MatchFields.vw_team_b))}"
        eml_date = f"{await match_record.get_field(MatchFields.match_date)}"
        eml_time = f"{await match_record.get_field(MatchFields.match_time_et)}"
        match_timestamp = f"{await match_record.get_field(MatchFields.match_timestamp)}"
        match_type = f"{await match_record.get_field(MatchFields.match_type)}"
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"Leauge Substitution Match Confirmed: {sub_player_mention} played for {our_team_mention} in a `{match_type}` match against {opponent_team_mention} on `{eml_date}` at `{eml_time}` ET `({match_timestamp})`.",
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
