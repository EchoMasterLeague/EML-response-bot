from database.database_full import FullDatabase
from database.fields import SuspensionFields, PlayerFields, TeamFields, TeamPlayerFields
from utils import discord_helpers, general_helpers
import discord
import logging

logger = logging.getLogger(__name__)


async def admin_suspend_player(
    database: FullDatabase,
    interaction: discord.Interaction,
    discord_member: discord.Member,
    reason: str,
    expiration_days: int,
):
    """Disable a command"""
    try:
        await interaction.response.defer(ephemeral=True)
        #######################################################################
        #                               RECORDS                               #
        #######################################################################
        # "Their" Player
        their_player_records = await database.table_player.get_player_records(
            discord_id=discord_member.id
        )
        their_player_record = their_player_records[0] if their_player_records else None
        # "Their" TeamPlayer
        their_teamplayer_records = (
            await database.table_team_player.get_team_player_records(
                player_id=discord_member.id
            )
        )
        their_teamplayer_record = (
            their_teamplayer_records[0] if their_teamplayer_records else None
        )
        # "Their" Team
        their_team_records = (
            await database.table_team.get_team_records(
                record_id=await their_teamplayer_record.get_field(
                    TeamPlayerFields.team_id
                )
            )
            if their_teamplayer_record
            else []
        )
        their_team_record = their_team_records[0] if their_team_records else None
        # "TheirTeam" TeamPlayers
        theirteam_teamplayers = (
            await database.table_team_player.get_team_player_records(
                team_id=await their_team_record.get_field(TeamFields.record_id)
            )
            if their_team_record
            else []
        )
        # "Their" (Existing) Suspension
        their_existing_suspension_records = (
            await database.table_suspension.get_suspension_records(
                player_id=discord_member.id
            )
        )
        their_existing_suspension_record = (
            their_existing_suspension_records[0]
            if their_existing_suspension_records
            else None
        )

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################

        # Delete Existing Suspension
        if their_existing_suspension_record:
            await database.table_suspension.delete_suspension_record(
                their_existing_suspension_record
            )
        # Create New Suspension
        new_suspension_record = (
            await database.table_suspension.create_suspension_record(
                player_id=discord_member.id,
                player_name=discord_member.display_name,
                reason=reason,
                expiration=expiration_days,
            )
        )
        assert new_suspension_record, f"Error: Failed to create suspension record."

        # Delete "Their" TeamPlayer
        if their_teamplayer_record:
            await database.table_team_player.delete_team_player_record(
                their_teamplayer_record
            )
        # Delete "Their" Player
        if their_player_record:
            await database.table_player.delete_player_record(their_player_record)
        # Remove All "Their" Discord League Roles
        await discord_helpers.member_remove_all_league_roles(member=discord_member)

        # Disband "Their" Team (if captain)
        if their_teamplayer_record:
            if await their_teamplayer_record.get_field(TeamPlayerFields.is_captain):
                # "TheirTeam" TeamPlayers
                their_player_id = await their_teamplayer_record.get_field(
                    TeamPlayerFields.player_id
                )
                for teammate_teamplayer in theirteam_teamplayers:
                    teammate_player_id = await teammate_teamplayer.get_field(
                        TeamPlayerFields.player_id
                    )
                    if teammate_player_id == their_player_id:
                        continue
                    # Delete TeamPlayer
                    await database.table_team_player.delete_team_player_record(
                        teammate_teamplayer
                    )
                    # Remove Discord Team Roles
                    await discord_helpers.member_remove_team_roles(
                        member=await discord_helpers.member_from_discord_id(
                            guild=interaction.guild,
                            discord_id=await teammate_teamplayer.get_field(
                                TeamPlayerFields.player_id
                            ),
                        ),
                    )
                # Team
                if their_team_record:
                    # Delete Team Record
                    await database.table_team.delete_team_record(their_team_record)
                    # Remove Discord Guild Team Role
                    await discord_helpers.guild_remove_team_role(
                        guild=interaction.guild,
                        team_name=await their_team_record.get_field(
                            TeamFields.team_name
                        ),
                    )

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        their_player_mention = f"{await discord_helpers.role_mention(guild=interaction.guild, discord_id=discord_member.id)}"
        suspension_expiration = (
            f"{await new_suspension_record.get_field(SuspensionFields.expires_at)}"
        )
        response_dictionary = {
            "player_id": f"{await new_suspension_record.get_field(SuspensionFields.player_id)}",
            "player_name": f"{await new_suspension_record.get_field(SuspensionFields.vw_player)}",
            "expires_at": f"{await new_suspension_record.get_field(SuspensionFields.expires_at)}",
            "reason": f"{await new_suspension_record.get_field(SuspensionFields.reason)}",
        }
        response_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(response_dictionary), "json"
        )
        await discord_helpers.final_message(
            interaction=interaction,
            message="\n".join(
                [
                    f"Suspension Created:\n{response_code_block}",
                    f"{their_player_mention} has been suspended until `{suspension_expiration}`.",
                ]
            ),
            ephemeral=True,
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################
        their_player_mention = f"{await discord_helpers.role_mention(guild=interaction.guild, discord_id=discord_member.id)}"
        suspension_expiration = (
            f"{await new_suspension_record.get_field(SuspensionFields.expires_at)}"
        )
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"{their_player_mention} has been suspended until `{suspension_expiration}`",
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.fail_message(interaction, message, ephemeral=True)
    except Exception as error:
        await discord_helpers.error_message(interaction, error, ephemeral=True)
