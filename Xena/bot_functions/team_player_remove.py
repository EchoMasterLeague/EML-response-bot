from database.database_full import FullDatabase
from database.fields import PlayerFields, TeamFields
from utils import discord_helpers, database_helpers
import discord


async def team_player_remove(
    database: FullDatabase,
    interaction: discord.Interaction,
    player_name: str,
):
    """Remove a Player from a Team by name"""
    try:
        # This could take a while
        await interaction.response.defer()
        # Get requestor's Team Details
        requestor_matches = await database.table_player.get_player_records(
            discord_id=interaction.user.id
        )
        assert_message = f"You register as a player, and be cpatin of a team to remove players from it."
        assert requestor_matches, assert_message
        requestor = requestor_matches[0]
        team_details = await database_helpers.get_team_details_from_player(
            database, requestor, assert_captain=True
        )
        assert (
            team_details
        ), f"You must be the captain of a team to remove players from it."
        # Verify Player exists
        players = await database.table_player.get_player_records(
            player_name=player_name
        )
        assert_message = f"Player `{player_name}` not found. Please check the spelling, and verify the player is registered."
        assert players, assert_message
        player = players[0]
        player_name = await player.get_field(PlayerFields.player_name)
        # Remove Player from Team
        player_id = await player.get_field(PlayerFields.record_id)
        team_id = await team_details.team.get_field(TeamFields.record_id)
        await database_helpers.remove_player_from_team(database, player_id, team_id)
        # Update Player's Discord roles
        player_discord_member = await discord_helpers.member_from_discord_id(
            guild=interaction.guild,
            discord_id=await player.get_field(PlayerFields.discord_id),
        )
        await discord_helpers.member_remove_team_roles(player_discord_member)
        # Update roster view
        await database_helpers.update_roster_view(database, team_id)
        # Success
        team_name = await team_details.team.get_field(TeamFields.team_name)
        message = f"Player `{player_name}` removed from team `{team_name}`."
        await discord_helpers.final_message(interaction, message)
        team_role = await discord_helpers.get_team_role(
            guild=interaction.guild, team_name=team_name
        )
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"{player_discord_member.mention} has been removed from {team_role.mention}",
        )
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
