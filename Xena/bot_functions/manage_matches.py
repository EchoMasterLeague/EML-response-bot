from database.fields import (
    PlayerFields,
    TeamFields,
    MatchInviteFields,
    MatchResultInviteFields,
    MatchFields,
)
from bot_dialogues import choices
from database.database_full import FullDatabase
from database.enums import MatchType, MatchResult, MatchStatus, InviteStatus
from database.records import MatchRecord, MatchResultInviteRecord
from errors.database_errors import EmlRecordAlreadyExists
from utils import discord_helpers, database_helpers, general_helpers
import constants
import datetime
import discord


class ManageMatches:
    """EML Match Management"""

    def __init__(self, database: FullDatabase):
        self._db = database

    async def send_match_invite(
        self,
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
            # Get inviter player details from discord_id
            inviter_player = await database_helpers.get_player_details_from_discord_id(
                self._db, interaction.user.id
            )
            inviter_player_id = await inviter_player.get_field(PlayerFields.record_id)
            # Get inviter team details from inviter player
            inviter_details: database_helpers.TeamDetailsOfPlayer
            inviter_details = await database_helpers.get_team_details_from_player(
                self._db, player=inviter_player, assert_any_captain=True
            )
            inviter_team = inviter_details.team
            inviter_team_id = await inviter_team.get_field(TeamFields.record_id)
            inviter_team_name = await inviter_team.get_field(TeamFields.team_name)
            # Get invitee team from opposing_team_name
            invitee_team = await self._db.table_team.get_team_record(
                team_name=opposing_team_name
            )
            assert invitee_team, f"Team '{opposing_team_name}' not found."
            inviter_player_name = await inviter_player.get_field(
                PlayerFields.player_name
            )
            invitee_team_id = await invitee_team.get_field(TeamFields.record_id)
            new_match_invite = (
                await self._db.table_match_invite.create_match_invite_record(
                    match_type=normalized_match_type,
                    match_epoch=match_epoch,
                    from_player_id=inviter_player_id,
                    from_team_id=inviter_team_id,
                    to_team_id=invitee_team_id,
                    vw_from_player=inviter_player_name,
                    vw_from_team=inviter_team_name,
                    vw_to_team=opposing_team_name,
                )
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
                clean_match_invite_dict[field] = full_match_invite_dict[field]
            match_invite_code_block = await discord_helpers.code_block(
                await general_helpers.format_json(clean_match_invite_dict), "json"
            )
            message = (
                f"Match Invite sent to {opposing_team_name}.\n{match_invite_code_block}"
            )
            await discord_helpers.final_message(interaction, message)
        except AssertionError as message:
            await discord_helpers.final_message(interaction, message)
        except EmlRecordAlreadyExists as message:
            await discord_helpers.final_message(interaction, message)
        except ValueError as error:
            message = f"Date/Time format is {constants.TIME_ENTRY_FORMAT}. {constants.TIMEZONE_ENCOURAGEMENT_MESSAGE}"
            await discord_helpers.final_message(interaction, message)
        except Exception as error:
            await discord_helpers.error_message(interaction, error)

    async def accept_match_invite(
        self,
        interaction: discord.Interaction,
        match_invite_id: str = None,
        log_channel: discord.TextChannel = None,
    ):
        try:
            if match_invite_id:
                # this could take a while, so defer the response
                await interaction.response.defer()
            # Get invitee player details from discord_id
            invitee_player = await database_helpers.get_player_details_from_discord_id(
                self._db, interaction.user.id
            )
            invitee_player_id = await invitee_player.get_field(PlayerFields.record_id)
            # Get invitee team details from invitee player
            invitee_details: database_helpers.TeamDetailsOfPlayer
            invitee_details = await database_helpers.get_team_details_from_player(
                self._db, player=invitee_player, assert_any_captain=True
            )
            invitee_team = invitee_details.team
            invitee_team_id = await invitee_team.get_field(TeamFields.record_id)
            # Get match invites for invitee team
            match_invites = await self._db.table_match_invite.get_match_invite_records(
                to_team_id=invitee_team_id
            )
            assert match_invites, f"No invites found."
            if not match_invite_id:
                # Get Options for the user to select
                match_offers = {}
                options_dict = {}
                option_number = 0
                for invite in match_invites:
                    option_number += 1
                    invite_id = await invite.get_field(MatchInviteFields.record_id)
                    match_type = await invite.get_field(MatchInviteFields.match_type)
                    team_name = await invite.get_field(MatchInviteFields.vw_from_team)
                    match_date = await invite.get_field(MatchInviteFields.match_date)
                    match_time = await invite.get_field(MatchInviteFields.match_time_et)
                    options_dict[invite_id] = f"Accept ({option_number})"
                    match_offers[str(option_number)] = {
                        "invite_id": invite_id,
                        "match_type": match_type,
                        "team": team_name,
                        "date": match_date,
                        "time_et": match_time,
                    }
                # Create the view to display the options
                view = choices.QuestionPromptView(
                    options_dict=options_dict,
                    initial_button_style=discord.ButtonStyle.success,
                )
                # Add option to clear invites
                clearall_button = choices.QuestionOptionButton(
                    label="Clear all invites",
                    style=discord.ButtonStyle.danger,
                    custom_id="clearall",
                )
                view.add_item(clearall_button)
                # Add option to cancel without making a choice
                cancel_button = choices.QuestionOptionButton(
                    label="Cancel",
                    style=discord.ButtonStyle.primary,
                    custom_id="cancel",
                )
                view.add_item(cancel_button)
                # Send the message with the options
                match_offers_json = await general_helpers.format_json(match_offers)
                match_offers_block = await discord_helpers.code_block(
                    match_offers_json, "json"
                )
                message = f"Match Invites:\n{match_offers_block}"
                message += "\nNote: All times in United States Eastern Time (ET)."
                message += "\n\nWarning: Once accepted, this cannot be undone."
                message += "\nFailure to show at scheduled time will result in automatic forfeiture."
                await interaction.response.send_message(
                    content=message, view=view, ephemeral=True
                )
                # Wait for the user to make a choice
                await view.wait()
                # Process the user's choice
                choice = view.value
                if not choice or choice == "cancel":
                    message = "No match selected."
                    return await discord_helpers.final_message(interaction, message)
                # clear invites
                if choice == "clearall":
                    for invite in match_invites:
                        await self._db.table_match_invite.delete_match_invite_record(
                            invite
                        )
                    message = "Match Invites cleared."
                    return await discord_helpers.final_message(interaction, message)
                # set match_invite_id to the user's choice
                match_invite_id = choice
            # Get the selected match invite
            selected_match_invite = None
            for match_invite in match_invites:
                invite_id = await match_invite.get_field(MatchInviteFields.record_id)
                if invite_id == match_invite_id:
                    selected_match_invite = match_invite
                    break
            assert selected_match_invite, f"Match Invite not found."
            # update match invite record
            await selected_match_invite.set_field(
                MatchInviteFields.invite_status, InviteStatus.ACCEPTED
            )
            await selected_match_invite.set_field(
                MatchInviteFields.to_player_id, invitee_player_id
            )
            await self._db.table_match_invite.update_match_invite_record(
                selected_match_invite
            )
            # get relevant fields from match invite
            inviter_team_id = await selected_match_invite.get_field(
                MatchInviteFields.from_team_id
            )
            match_timestamp = await selected_match_invite.get_field(
                MatchInviteFields.match_timestamp
            )
            match_epoch = await general_helpers.epoch_timestamp(match_timestamp)
            match_type = await selected_match_invite.get_field(
                MatchInviteFields.match_type
            )
            # create match record
            inviter_team_id = await selected_match_invite.get_field(
                MatchInviteFields.from_team_id
            )
            inviter_team = await self._db.table_team.get_team_record(
                record_id=inviter_team_id
            )
            inviter_team_name = await inviter_team.get_field(TeamFields.team_name)
            invitee_team = await self._db.table_team.get_team_record(
                record_id=invitee_team_id
            )
            invitee_team_name = await invitee_team.get_field(TeamFields.team_name)
            new_match = await self._db.table_match.create_match_record(
                team_a_id=inviter_team_id,
                team_b_id=invitee_team_id,
                match_epoch=match_epoch,
                match_type=match_type,
                vw_team_a=inviter_team_name,
                vw_team_b=invitee_team_name,
            )
            assert new_match, f"Error: Failed to create match record."
            # delete match invite record
            await self._db.table_match_invite.delete_match_invite_record(
                selected_match_invite
            )
            # success
            fields_to_show = [
                MatchFields.vw_team_a,
                MatchFields.vw_team_b,
                MatchFields.match_date,
                MatchFields.match_time_et,
                MatchFields.match_type,
            ]
            full_new_match_dict = await new_match.to_dict()
            clean_new_match_dict = {}
            for field in fields_to_show:
                clean_new_match_dict[field] = full_new_match_dict[field]
            match_code_block = await discord_helpers.code_block(
                await general_helpers.format_json(clean_new_match_dict), "json"
            )
            message = f"Match Invite accepted. Match created.\n{match_code_block}"
            message += f"\n\nRemember: This cannot be undone. Failure to show will result in automatic forfeiture."
            await discord_helpers.final_message(interaction, message)
            team_a_role = await discord_helpers.get_team_role(
                guild=interaction.guild, team_name=inviter_team_name
            )
            team_b_role = await discord_helpers.get_team_role(
                guild=interaction.guild, team_name=invitee_team_name
            )
            eml_date = await new_match.get_field(MatchFields.match_date)
            eml_time = await new_match.get_field(MatchFields.match_time_et)
            log_message = f"{team_a_role.mention} and {team_b_role.mention} have a `{match_type}` match scheduled for `{eml_date}` at `{eml_time}` (`{match_timestamp}`)"
            await discord_helpers.log_to_channel(
                channel=log_channel, message=log_message
            )
        except AssertionError as message:
            await discord_helpers.final_message(interaction, message)
        except Exception as error:
            await discord_helpers.error_message(interaction, error)

    async def revoke_match_invite(self, interaction: discord.Interaction):
        pass

    async def send_result_invite(
        self,
        interaction: discord.Interaction,
        opposing_team_name: str,
        scores: list[tuple[int, int]],
        outcome: str,
        match_type: str = MatchType.ASSIGNED.value,
    ):
        try:
            # this could take a while, so defer the response
            await interaction.response.defer()
            # constants
            # message_score_format = "Score format: '1a:1b,2a:2b,3a:3b' (you are team a) e.g. '7:5,4:6,6:4' means you won 7-5, lost 4-6, won 6-4"
            message_outcome_mistmatch = "The scores and outcome do not match. Please ensure you are entering the data with your team's scores first for each round."
            message_warning = "Warning: Once accepted, this cannot be undone."
            # Get inviter player details from discord_id
            inviter_player = await database_helpers.get_player_details_from_discord_id(
                self._db, interaction.user.id
            )
            inviter_player_id = await inviter_player.get_field(PlayerFields.record_id)
            # Get inviter team details from inviter player
            inviter_team_details: database_helpers.TeamDetailsOfPlayer
            inviter_team_details = await database_helpers.get_team_details_from_player(
                self._db, player=inviter_player, assert_any_captain=True
            )
            inviter_team = inviter_team_details.team
            inviter_team_id = await inviter_team.get_field(TeamFields.record_id)
            inviter_team_name = await inviter_team.get_field(TeamFields.team_name)
            # Get invitee team details from opposing_team_name
            invitee_team = await self._db.table_team.get_team_record(
                team_name=opposing_team_name
            )
            invitee_team_details = await database_helpers.get_team_details_from_team(
                self._db, team=invitee_team
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
                    "tied".casefold(),
                    "draw".casefold(),
                    "drawn".casefold(),
                    "equal".casefold(),
                ]:
                    result = MatchResult.DRAW
                if outcome.casefold() in [
                    "win".casefold(),
                    "won".casefold(),
                    "winner".casefold(),
                    "victor".casefold(),
                    "victory".casefold(),
                    "victorious".casefold(),
                ]:
                    result = MatchResult.WIN
                if outcome.casefold() in [
                    "lose".casefold(),
                    "loss".casefold(),
                    "lost".casefold(),
                    "loser".casefold(),
                    "defeat".casefold(),
                    "defeated".casefold(),
                ]:
                    result = MatchResult.LOSS
            assert_message = f"Outcome must be one of: [{', '.join([str(option.value) for option in MatchResult])}]"
            assert result, assert_message
            # verify scores input matches format "1a:1b,2a:2b,3a:3b" with regex
            # regex_score_format = r"^\d+:\d+(,\d+:\d+){1,2}$"
            # is_valid_score_inptut = re.match(regex_score_format, scores)
            # assert_message = "Score format: '1a:1b,2a:2b,3a:3b' (you are team a) e.g. '7:5,4:6,6:4' means you won 7-5, lost 4-6, won 6-4"
            # assert is_valid_score_inptut, assert_message
            # parse scores from "1a:1b,2a:2b,3a:3b" to [["1a", "1b"], ["2a", "2b"], ["3a", "3b"]] and ensure they are integers
            # rounds_array = scores.split(",")
            # scores_list = []
            # for round in rounds_array:
            #    score_array = round.split(":")
            #    score_a = int(score_array[0])
            #    score_b = int(score_array[1])
            #    scores_list.append([score_a, score_b])
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
            matches = await self._db.table_match.get_match_records(
                team_a_id=inviter_team_id,
                team_b_id=invitee_team_id,
                match_type=match_type,
                match_status=MatchStatus.PENDING.value,
            )
            reverse_matches = await self._db.table_match.get_match_records(
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
            # create match result invite record
            match_id = await match_record.get_field(MatchFields.record_id)
            match_type = await match_record.get_field(MatchFields.match_type)
            inviter_player_name = await inviter_player.get_field(
                PlayerFields.player_name
            )
            new_result_invite: MatchResultInviteRecord = (
                await self._db.table_match_result_invite.create_match_result_invite_record(
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
            # success
            fields_to_show = [
                MatchResultInviteFields.vw_from_team,
                MatchResultInviteFields.vw_to_team,
                MatchResultInviteFields.match_outcome,
                MatchResultInviteFields.round_1_score_a,
                MatchResultInviteFields.round_1_score_b,
                MatchResultInviteFields.round_2_score_a,
                MatchResultInviteFields.round_2_score_b,
                MatchResultInviteFields.round_3_score_a,
                MatchResultInviteFields.round_3_score_b,
                MatchResultInviteFields.match_type,
            ]
            full_new_result_invite_dict = await new_result_invite.to_dict()
            clean_new_result_invite_dict = {}
            for field in fields_to_show:
                clean_new_result_invite_dict[field] = full_new_result_invite_dict[field]
            invite_code_block = await discord_helpers.code_block(
                f"{await general_helpers.format_json(clean_new_result_invite_dict)}",
                "json",
            )
            message = f"Match Result Invite sent to {opposing_team_name}.\n{invite_code_block}"
            await discord_helpers.final_message(interaction, message)
        except AssertionError as message:
            await discord_helpers.final_message(interaction, message)
        except EmlRecordAlreadyExists as message:
            await discord_helpers.final_message(interaction, message)
        except Exception as error:
            await discord_helpers.error_message(interaction, error)

    async def accept_result_invite(
        self, interaction: discord.Interaction, log_channel: discord.TextChannel = None
    ):
        """Accept a Match Result Invite"""
        try:
            # this could take a while, so defer the response
            # await interaction.response.defer()
            # Get invitee player details from discord_id
            invitee_player = await database_helpers.get_player_details_from_discord_id(
                self._db, interaction.user.id
            )
            invitee_player_id = await invitee_player.get_field(PlayerFields.record_id)
            # Get invitee team details from invitee player
            invitee_details: database_helpers.TeamDetailsOfPlayer
            invitee_details = await database_helpers.get_team_details_from_player(
                self._db, player=invitee_player, assert_any_captain=True
            )
            invitee_team = invitee_details.team
            invitee_team_id = await invitee_team.get_field(TeamFields.record_id)
            # Get match result invites for invitee team
            match_result_invites = await self._db.table_match_result_invite.get_match_result_invite_records(
                to_team_id=invitee_team_id
            )
            assert (
                match_result_invites
            ), f"No match results availavble to confirm. You may want to create a result offer for another team."
            # Get Options for the user to select
            match_result_offers = {}
            options_dict = {}
            option_number = 0
            for invite in match_result_invites:
                option_number += 1
                invite_id = await invite.get_field(MatchInviteFields.record_id)
                # reverse scores
                scores = [
                    (
                        await invite.get_field(MatchResultInviteFields.round_1_score_b),
                        await invite.get_field(MatchResultInviteFields.round_1_score_a),
                    ),
                    (
                        await invite.get_field(MatchResultInviteFields.round_2_score_b),
                        await invite.get_field(MatchResultInviteFields.round_2_score_a),
                    ),
                    (
                        await invite.get_field(MatchResultInviteFields.round_3_score_b),
                        await invite.get_field(MatchResultInviteFields.round_3_score_a),
                    ),
                ]
                scores_dict = {
                    "round_1": f"{scores[0][0]: >3} : {scores[0][1]: >3}",
                    "round_2": f"{scores[1][0]: >3} : {scores[1][1]: >3}",
                    "round_3": f"{scores[2][0]: >3} : {scores[2][1]: >3}",
                }
                if scores_dict["round_3"] == " : ":
                    scores_dict["round_3"] = "Not played"
                # reverse outcome
                outcome = await invite.get_field(MatchResultInviteFields.match_outcome)
                match_type = await invite.get_field(MatchResultInviteFields.match_type)
                team_name = await invite.get_field(MatchResultInviteFields.vw_from_team)
                if outcome == MatchResult.WIN:
                    outcome = MatchResult.LOSS
                elif outcome == MatchResult.LOSS:
                    outcome = MatchResult.WIN
                options_dict[invite_id] = f"Accept ({option_number})"
                match_result_offers[str(option_number)] = {
                    "invite_id": invite_id,
                    "match_type": match_type,
                    "team": team_name,
                    "outcome": outcome,
                    "scores": scores_dict,
                }
            # Create the view to display the options
            view = choices.QuestionPromptView(
                options_dict=options_dict,
                initial_button_style=discord.ButtonStyle.success,
            )
            # Add option to clear invites
            clearall_button = choices.QuestionOptionButton(
                label="Clear all invites",
                style=discord.ButtonStyle.danger,
                custom_id="clearall",
            )
            view.add_item(clearall_button)
            # Add option to cancel without making a choice
            cancel_button = choices.QuestionOptionButton(
                label="Cancel",
                style=discord.ButtonStyle.primary,
                custom_id="cancel",
            )
            view.add_item(cancel_button)
            # Send the message with the options
            match_result_offers_json = await general_helpers.format_json(
                match_result_offers
            )
            match_result_offers_block = await discord_helpers.code_block(
                match_result_offers_json, "json"
            )
            message = f"Match Result Invites:\n{match_result_offers_block}"
            message += "\n\nWarning: Once accepted, this cannot be undone."
            await interaction.response.send_message(
                content=message, view=view, ephemeral=True
            )
            # Wait for the user to make a choice
            await view.wait()
            # Process the user's choice
            choice = view.value
            if not choice or choice == "cancel":
                message = "No match result selected."
                return await discord_helpers.final_message(interaction, message)
            # clear invites
            if choice == "clearall":
                for invite in match_result_invites:
                    await self._db.table_match_result_invite.delete_match_result_invite_record(
                        invite
                    )
                message = "Match Result Invites cleared."
                return await discord_helpers.final_message(interaction, message)
            # Get the selected match result invite
            selected_invite = None
            for match_result_invite in match_result_invites:
                invite_id = await match_result_invite.get_field(
                    MatchResultInviteFields.record_id
                )
                if invite_id == choice:
                    selected_invite = match_result_invite
                    break
            assert selected_invite, f"Match Result Invite not found."
            # update match result invite record
            await selected_invite.set_field(
                MatchResultInviteFields.invite_status, InviteStatus.ACCEPTED
            )
            await selected_invite.set_field(
                MatchResultInviteFields.to_player_id, invitee_player_id
            )
            await self._db.table_match_result_invite.update_match_result_invite_record(
                selected_invite
            )
            # get relevant fields from match record
            match_id = await selected_invite.get_field(MatchResultInviteFields.match_id)
            match_records = await self._db.table_match.get_match_records(
                record_id=match_id
            )
            assert match_records, f"Error: Failed to find match record."
            match_record = match_records[0]
            team_a_id = await match_record.get_field(MatchFields.team_a_id)
            team_b_id = await match_record.get_field(MatchFields.team_b_id)
            # get relevant fields from match results invite record
            # get relevant fields from match result invite
            inviter_team_id = await selected_invite.get_field(
                MatchResultInviteFields.from_team_id
            )
            invitee_team_id = await selected_invite.get_field(
                MatchResultInviteFields.to_team_id
            )

            outcome = outcome = await selected_invite.get_field(
                MatchResultInviteFields.match_outcome
            )
            scores = [
                [
                    await selected_invite.get_field(
                        MatchResultInviteFields.round_1_score_a
                    ),
                    await selected_invite.get_field(
                        MatchResultInviteFields.round_1_score_b
                    ),
                ],
                [
                    await selected_invite.get_field(
                        MatchResultInviteFields.round_2_score_a
                    ),
                    await selected_invite.get_field(
                        MatchResultInviteFields.round_2_score_b
                    ),
                ],
                [
                    await selected_invite.get_field(
                        MatchResultInviteFields.round_3_score_a
                    ),
                    await selected_invite.get_field(
                        MatchResultInviteFields.round_3_score_b
                    ),
                ],
            ]
            # reverse scores and oucome if the teams are listed the other way in the match record
            if team_a_id == invitee_team_id:
                scores = [
                    [scores[0][1], scores[0][0]],
                    [scores[1][1], scores[1][0]],
                    [scores[2][1], scores[2][0]],
                ]
                if outcome == MatchResult.WIN:
                    outcome = MatchResult.LOSS
                elif outcome == MatchResult.LOSS:
                    outcome = MatchResult.WIN
            # update match record
            await match_record.set_field(
                MatchFields.match_status, MatchStatus.COMPLETED.value
            )
            await match_record.set_field(MatchFields.round_1_score_a, scores[0][0])
            await match_record.set_field(MatchFields.round_1_score_b, scores[0][1])
            await match_record.set_field(MatchFields.round_2_score_a, scores[1][0])
            await match_record.set_field(MatchFields.round_2_score_b, scores[1][1])
            await match_record.set_field(MatchFields.round_3_score_a, scores[2][0])
            await match_record.set_field(MatchFields.round_3_score_b, scores[2][1])
            await match_record.set_field(MatchFields.outcome, outcome)
            match_record = MatchRecord(await match_record.to_list())  # normalize
            await self._db.table_match.update_match_record(match_record)
            # Update match result invite record
            await selected_invite.set_field(
                MatchResultInviteFields.invite_status, InviteStatus.ACCEPTED
            )
            await selected_invite.set_field(
                MatchResultInviteFields.to_player_id, invitee_player_id
            )
            await self._db.table_match_result_invite.update_match_result_invite_record(
                selected_invite
            )
            # delete match result invite record
            await self._db.table_match_result_invite.delete_match_result_invite_record(
                selected_invite
            )
            # success
            match_code_block = await discord_helpers.code_block(
                await general_helpers.format_json(await match_record.to_dict()), "json"
            )
            message = f"Match Result Invite accepted.\n{match_code_block}\nMatch results confirmed."
            await discord_helpers.final_message(interaction, message)
            # [@TEAM A] "wins against" or "loses to" [@TEAM B]
            team_a_name = await match_record.get_field(MatchFields.vw_team_a)
            team_b_name = await match_record.get_field(MatchFields.vw_team_b)
            team_a_role = await discord_helpers.get_team_role(
                guild=interaction.guild, team_name=team_a_name
            )
            team_b_role = await discord_helpers.get_team_role(
                guild=interaction.guild, team_name=team_b_name
            )
            outcomes = "draws with"
            outcomes = "wins against" if outcome == MatchResult.WIN else outcomes
            outcomes = "loses to" if outcome == MatchResult.LOSS else outcomes
            await discord_helpers.log_to_channel(
                channel=log_channel,
                message=f"{team_a_role.mention} {outcomes} {team_b_role.mention} in a `{match_type}` match",
            )

        except AssertionError as message:
            await discord_helpers.final_message(interaction, message)
        except Exception as error:
            await discord_helpers.error_message(interaction, error)

    async def revoke_result_invite(self, interaction: discord.Interaction):
        pass
