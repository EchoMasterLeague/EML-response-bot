from database.database_full import FullDatabase
from database.fields import SuspensionFields, PlayerFields, TeamFields, TeamPlayerFields
from utils import discord_helpers, general_helpers
import discord


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
        assert their_player_records, f"Player not found."
        their_player_record = their_player_records[0]
        # "Their" TeamPlayer
        their_team_player_records = (
            await database.table_team_player.get_team_player_records(
                player_id=await their_player_record.get_field(PlayerFields.record_id)
            )
        )
        their_team_player_record = (
            their_team_player_records[0] if their_team_player_records else None
        )
        # "Their" Team
        their_team_records = (
            await database.table_team.get_team_records(
                record_id=await their_team_player_record.get_field(
                    PlayerFields.record_id
                )
            )
            if their_team_player_record
            else None
        )
        their_team_record = their_team_records[0] if their_team_records else None
        # "Their" Suspension
        their_existing_suspension_records = (
            await database.table_suspension.get_suspension_records(
                player_id=await their_player_record.get_field(
                    SuspensionFields.record_id
                )
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
        new_suspension_record = await database.table_suspension.create_suspension_record(
            player_id=await their_player_record.get_field(PlayerFields.record_id),
            player_name=f"{await their_player_record.get_field(PlayerFields.player_name)}",
            reason=reason,
            expiration=expiration_days,
        )
        assert new_suspension_record, f"Error: Failed to create suspension record."

        # Delete "Their" TeamPlayer
        if their_team_player_record:
            await database.table_team_player.delete_team_player_record(
                their_team_player_record
            )

        # Delete "Their" Player
        if their_player_record:
            await database.table_player.delete_player_record(their_player_record)

        # Disband "Their" Team (if captain)
        if their_team_player_record:
            # Team
            if their_team_record:
                await database.table_team.delete_team_record(their_team_record)
            # TeamPlayers
            if await their_team_player_record.get_field(TeamPlayerFields.is_captain):
                teammates = await database.table_team_player.get_team_player_records(
                    team_id=await their_team_player_record.get_field(
                        TeamPlayerFields.team_id
                    )
                )
                for teammate in teammates:
                    await database.table_team_player.delete_team_player_record(teammate)

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        their_player_mention = f"{await discord_helpers.role_mention(guild=interaction.guild, discord_id=discord_member.id)}"
        their_team_mention = (
            f"{await discord_helpers.role_mention(guild=interaction.guild, team_name=await their_team_record.get_field(TeamFields.team_name))}"
            if their_team_record
            else None
        )
        suspended = "suspended"
        if their_team_mention:
            suspended += f" and removed from {their_team_mention}"
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
                    f"{discord_member.mention} has been {suspended} until `{suspension_expiration}`.",
                ]
            ),
            ephemeral=True,
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################
        their_player_mention = f"{await discord_helpers.role_mention(guild=interaction.guild, discord_id=discord_member.id)}"
        their_team_mention = (
            f"{await discord_helpers.role_mention(guild=interaction.guild, team_name=await their_team_record.get_field(TeamFields.team_name))}"
            if their_team_record
            else None
        )
        suspended = "suspended"
        if their_team_mention:
            suspended += f" and removed from {their_team_mention}"
        suspension_expiration = (
            f"{await new_suspension_record.get_field(SuspensionFields.expires_at)}"
        )
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"{their_player_mention} has been {suspended} until `{suspension_expiration}`",
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message, ephemeral=True)
    except Exception as error:
        await discord_helpers.error_message(interaction, error, ephemeral=True)
