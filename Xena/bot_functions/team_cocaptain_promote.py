from database.database_full import FullDatabase
from database.fields import PlayerFields, TeamPlayerFields
from utils import discord_helpers, database_helpers
import discord


async def team_cocaptain_promote(
    database: FullDatabase,
    interaction: discord.Interaction,
    player_name: str,
    log_channel: discord.TextChannel = None,
):
    """Promote a Player to Team co-captain"""
    try:
        # This could take a while
        await interaction.response.defer()
        # Get info about the requestor
        requestor_matches = await database.table_player.get_player_records(
            discord_id=interaction.user.id
        )
        assert (
            requestor_matches
        ), f"You must be registered as a player to promote players."
        requestor = requestor_matches[0]
        requestor_id = await requestor.get_field(PlayerFields.record_id)
        requestor_team_players = (
            await database.table_team_player.get_team_player_records(
                player_id=requestor_id
            )
        )
        assert requestor_team_players, f"You must be on a team to promote players."
        requestor_team_player = requestor_team_players[0]
        requestor_is_captain = await requestor_team_player.get_field(
            TeamPlayerFields.is_captain
        )
        assert requestor_is_captain, f"You must be team captain to promote players."
        # Get info about the Team
        team_id = await requestor_team_player.get_field(TeamPlayerFields.team_id)
        team_players = await database.table_team_player.get_team_player_records(
            team_id=team_id
        )
        # Get info about co-captain
        co_captain_id = None
        for team_player in team_players:
            if await team_player.get_field(TeamPlayerFields.is_co_captain):
                co_captain_id = await team_player.get_field(TeamPlayerFields.player_id)
        assert not co_captain_id, f"Team already has a co-captain."
        # Get info about the Player
        players = await database.table_player.get_player_records(
            player_name=player_name
        )
        assert players, f"Player not found."
        player = players[0]
        player_name = await player.get_field(PlayerFields.player_name)
        player_id = await player.get_field(PlayerFields.record_id)
        player_team_player = None
        for team_player in team_players:
            if await team_player.get_field(TeamPlayerFields.player_id) == player_id:
                player_team_player = team_player
        assert player_team_player, f"Player is not on the team."
        assert player_id != requestor_id, f"Cannot promote yourself."
        # Update Player's TeamPlayer record
        await player_team_player.set_field(TeamPlayerFields.is_co_captain, True)
        await database.table_team_player.update_team_player_record(player_team_player)
        # Update Player's Discord roles
        region = await requestor.get_field(PlayerFields.region)
        player_discord_id = await player.get_field(PlayerFields.discord_id)
        player_discord_member = await discord_helpers.member_from_discord_id(
            guild=interaction.guild,
            discord_id=player_discord_id,
        )
        await discord_helpers.member_add_co_captain_role(player_discord_member, region)
        # Update roster view
        await database_helpers.update_roster_view(database, team_id)
        # Success
        message = f"Player '{player_name}' promoted to co-captain"
        await discord_helpers.final_message(interaction, message)
        await discord_helpers.log_to_channel(
            channel=log_channel,
            message=f"{player_discord_member.mention} is now Co-Captain",
        )
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
