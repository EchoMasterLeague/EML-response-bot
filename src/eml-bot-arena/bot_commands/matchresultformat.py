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
from database.records import MatchRecord, PlayerRecord
from utils import discord_helpers, database_helpers, general_helpers, match_helpers
import discord
import constants
import json


async def match_result_format(
    database: FullDatabase,
    interaction: discord.Interaction,
):
    """Accept a Match Result Invite"""
    try:
        #######################################################################
        #                               RECORDS                               #
        #######################################################################
        # Match
        match_records = await database.table_match.get_match_records(
            record_id="e95442cf-fd68-4b8d-adeb-b2968c7dd9b3"
        )
        assert match_records, f"Match record not found."
        match_record = match_records[0]

        # "A" Team
        team_a_records = await database.table_team.get_team_records(
            record_id=await match_record.get_field(MatchFields.team_a_id)
        )
        assert team_a_records, f"Team A record not found."
        team_a_record = team_a_records[0]
        # "B" Team
        team_b_records = await database.table_team.get_team_records(
            record_id=await match_record.get_field(MatchFields.team_b_id)
        )
        assert team_b_records, f"Team B record not found."
        team_b_record = team_b_records[0]

        # "A" Players
        team_a_teamplayer_records = (
            await database.table_team_player.get_team_player_records(
                team_id=await match_record.get_field(MatchFields.team_a_id)
            )
        )
        team_a_player_records_dict: dict[str, PlayerRecord] = {}
        for teamplayer_record in team_a_teamplayer_records:
            player_records = await database.table_player.get_player_records(
                record_id=await teamplayer_record.get_field(TeamPlayerFields.player_id)
            )
            if player_records:
                player_record = player_records[0]
                name = await player_record.get_field(PlayerFields.player_name)
                team_a_player_records_dict[name] = player_record
        team_a_player_records_dict = dict(sorted(team_a_player_records_dict.items()))
        # "B" Players
        team_b_teamplayer_records = (
            await database.table_team_player.get_team_player_records(
                team_id=await match_record.get_field(MatchFields.team_b_id)
            )
        )
        team_b_player_records_dict: dict[str, PlayerRecord] = {}
        for teamplayer_record in team_b_teamplayer_records:
            player_records = await database.table_player.get_player_records(
                record_id=await teamplayer_record.get_field(TeamPlayerFields.player_id)
            )
            if player_records:
                player_record = player_records[0]
                name = await player_record.get_field(PlayerFields.player_name)
                team_b_player_records_dict[name] = player_record
        team_b_player_records_dict = dict(sorted(team_b_player_records_dict.items()))

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################
        scores = await match_record.get_scores()
        assert scores, f"Match scores not found."
        if MatchResult.WIN != await match_record.get_field(MatchFields.outcome):
            scores = await match_helpers.get_reversed_scores(scores)
            team_a_record, team_b_record = team_b_record, team_a_record
            team_a_player_records_dict, team_b_player_records_dict = (
                team_b_player_records_dict,
                team_a_player_records_dict,
            )

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        await interaction.response.send_message(content="ok", ephemeral=True)

        #######################################################################
        #                               LOGGING                               #
        #######################################################################
        # Also log in the match-results channel
        team_a_name = await team_a_record.get_field(TeamFields.team_name)
        team_b_name = await team_b_record.get_field(TeamFields.team_name)
        team_a_player_mentions = []
        for player_record in team_a_player_records_dict.values():
            team_a_player_mentions.append(
                f"{await discord_helpers.role_mention(guild=interaction.guild,discord_id=await player_record.get_field(PlayerFields.discord_id))}"
            )
        team_b_player_mentions = []
        for player_record in team_b_player_records_dict.values():
            team_b_player_mentions.append(
                f"{await discord_helpers.role_mention(guild=interaction.guild,discord_id=await player_record.get_field(PlayerFields.discord_id))}"
            )
        scores = await match_record.get_scores()
        match_type = await match_record.get_field(MatchFields.match_type)
        rounds = 0
        for score in scores:
            if score and score[0] != None and score[1] != None:
                rounds += 1
        for i in range(len(scores)):
            for j in range(len(scores[i])):
                if scores[i][j] == None:
                    scores[i][j] = "_"

        embed = discord.Embed(
            description=f"**{team_a_name}** Wins vs **{team_b_name}** in (`{rounds}`) Rounds",
            color=discord.Colour.green(),
        )

        embed.add_field(
            name="Round Scores",
            value="\n".join(
                [
                    f"- Round 1:  (`{scores[0][0]}` to `{scores[0][1]}`)",
                    f"- Round 2:  (`{scores[1][0]}` to `{scores[1][1]}`)",
                    f"- Round 3:  (`{scores[2][0]}` to `{scores[2][1]}`)",
                ]
            ),
            inline=True,
        )
        embed.add_field(
            name="Match Type",
            value="\n".join(
                [
                    f"- {match_type}",
                    "",
                    f"[Rankings](https://echomasterleague.com/2024-season-1-team-rankings/)",
                ],
            ),
            inline=True,
        )
        await discord_helpers.log_to_channel(
            interaction=interaction,
            channel_name=constants.DISCORD_CHANNEL_MATCH_RESULTS,
            message="\n".join(
                [
                    f"[{team_a_name}]: {', '.join(team_a_player_mentions)}",
                    f"[{team_b_name}]: {', '.join(team_b_player_mentions)}",
                ]
            ),
            embed=embed,
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
