from database.database_full import FullDatabase
from database.fields import CooldownFields, PlayerFields, TeamFields, TeamPlayerFields, SuspensionFields
from database.records import CooldownRecord
from utils import discord_helpers, general_helpers
import discord


async def show_player_details(
    database: FullDatabase,
    interaction: discord.Interaction,
    discord_member: discord.Member,
):
    """Show Details of a Player"""
    try:
        await interaction.response.defer()
        #######################################################################
        #                               RECORDS                               #
        #######################################################################
        # Suspension
        suspension_records = await database.table_suspension.get_suspension_records(
            player_id=discord_member.id
        )
        suspension_record = suspension_records[0] if suspension_records else None
        assert not suspension_record, f"Player {discord_member.mention} is suspended until {await suspension_record.get_field(SuspensionFields.expires_at)}."
        # Player
        player_records = await database.table_player.get_player_records(
            discord_id=discord_member.id
        )
        assert player_records, f"Player `{discord_member.display_name}` not found. Are they registered?"
        player_record = player_records[0]
        # TeamPlayer
        teamplayer_records = await database.table_team_player.get_team_player_records(
            player_id=await player_record.get_field(PlayerFields.record_id)
        )
        teamplayer_record = teamplayer_records[0] if teamplayer_records else None
        # Team
        team_records = (
            await database.table_team.get_team_records(
                record_id=await teamplayer_record.get_field(TeamPlayerFields.team_id)
            )
            if teamplayer_record
            else None
        )
        team_record = team_records[0] if team_records else None
        # Cooldown
        cooldown_records = await database.table_cooldown.get_cooldown_records(
            player_id=await player_record.get_field(PlayerFields.record_id)
        )
        cooldown_record = cooldown_records[0] if cooldown_records else None

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################
        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        response_dictionary = {
            "player": await player_record.get_field(PlayerFields.player_name),
            "region": await player_record.get_field(PlayerFields.region),
            "cooldown_end": f"{await cooldown_record.get_field(CooldownFields.expires_at)}" if cooldown_record else None,
            "team": f"{await team_record.get_field(TeamFields.team_name)}" if team_record else None,
            "team_role": f"{"captain" if await teamplayer_record.get_field(TeamPlayerFields.is_captain) else "co-captain" if await teamplayer_record.get_field(TeamPlayerFields.is_co_captain) else "member"}" if teamplayer_record else None,
        }
        if not response_dictionary["cooldown_end"]:
            response_dictionary.pop("cooldown_end")
        response_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(response_dictionary), "json"
        )
        await discord_helpers.final_message(
            interaction=interaction,
            message="\n".join(
                [
                    f"{response_code_block}",
                ]
            ),
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
