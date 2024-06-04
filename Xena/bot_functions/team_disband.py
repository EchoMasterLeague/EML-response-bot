from database.database_full import FullDatabase
from database.fields import PlayerFields, TeamPlayerFields, TeamFields
from utils import discord_helpers, database_helpers
import discord


async def team_disband(
    database: FullDatabase,
    interaction: discord.Interaction,
    log_channel: discord.TextChannel = None,
):
    """Disband the requestor's Team"""
    try:
        # This could take a while
        await interaction.response.defer()
        # Get info about the requestor
        requestor_matches = await database.table_player.get_player_records(
            discord_id=interaction.user.id
        )
        assert (
            requestor_matches
        ), f"You must be registered as a player to disband a team."
        requestor = requestor_matches[0]
        requestor_id = await requestor.get_field(PlayerFields.record_id)
        requestor_team_players = (
            await database.table_team_player.get_team_player_records(
                player_id=requestor_id
            )
        )
        assert requestor_team_players, f"You must be on a team to disband it."
        requestor_team_player = requestor_team_players[0]
        requestor_is_captain = await requestor_team_player.get_field(
            TeamPlayerFields.is_captain
        )
        assert requestor_is_captain, f"You must be team captain to disband a team."
        # Get info about the Team
        team_id = await requestor_team_player.get_field(TeamPlayerFields.team_id)
        teams = await database.table_team.get_team_records(record_id=team_id)
        assert teams, f"Team not found."
        team = teams[0]
        team_name = await team.get_field(TeamFields.team_name)
        team_players = await database.table_team_player.get_team_player_records(
            team_id=team_id
        )
        # Remove all Players from the Team
        discord_members: list[discord.Member] = []
        for team_player in team_players:
            # Remove Player's Discord roles
            player_id = await team_player.get_field(TeamPlayerFields.player_id)
            players = await database.table_player.get_player_records(
                record_id=player_id
            )
            assert players, f"Player not found."
            player = players[0]
            player_discord_id = await player.get_field(PlayerFields.discord_id)
            player_discord_member = await discord_helpers.member_from_discord_id(
                guild=interaction.guild,
                discord_id=player_discord_id,
            )
            discord_members.append(player_discord_member)
            await discord_helpers.member_remove_team_roles(player_discord_member)
            # Apply cooldown
            player_name = await player.get_field(PlayerFields.player_name)
            new_cooldown = await database.table_cooldown.create_cooldown_record(
                player_id=player_id,
                old_team_id=team_id,
                player_name=player_name,
                old_team_name=team_name,
            )
            assert new_cooldown, f"Error: Could not apply cooldown."
            # Remove the Player from the Team
            await database.table_team_player.delete_team_player_record(team_player)
        # Delete the Team
        await database.table_team.delete_team_record(team)
        await discord_helpers.guild_remove_team_role(interaction.guild, team_name)
        # Update roster view
        await database_helpers.update_roster_view(database, team_id)
        # Success
        user_message = f"Team '{team_name}' has been disbanded"
        await discord_helpers.final_message(interaction, user_message)
        captain_discord = interaction.user
        discord_members.remove(captain_discord)
        players = ", ".join([member.mention for member in discord_members])
        await discord_helpers.log_to_channel(
            channel=log_channel,
            message=f"`{team_name}` has been disbanded by {captain_discord.mention}, removing [{players}]",
        )
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
