from database.database_full import FullDatabase
from database.fields import CooldownFields, PlayerFields, TeamFields, TeamPlayerFields
from database.records import CooldownRecord
from utils import discord_helpers, general_helpers
import discord


async def show_player_details(
    database: FullDatabase,
    interaction: discord.Interaction,
    player_name: str = None,
    discord_id: str = None,
):
    """Show Details of a Player"""
    try:
        # This could take a while
        await interaction.response.defer()
        # Get Player info
        if not discord_id and not player_name:
            discord_id = interaction.user.id
        players = await database.table_player.get_player_records(
            discord_id=discord_id, player_name=player_name
        )
        assert players, "Player not found."
        message_data = []
        for player in players:
            player_name = await player.get_field(PlayerFields.player_name)
            player_region = await player.get_field(PlayerFields.region)
            player_id = await player.get_field(PlayerFields.record_id)
            message_dict = {}
            message_dict["player"] = player_name
            message_dict["region"] = player_region
            # Get cooldown info
            cooldowns = await database.table_cooldown.get_cooldown_records(
                player_id=player_id
            )
            cooldown: CooldownRecord = cooldowns[0] if cooldowns else None
            if cooldown:
                cooldown_end = await cooldown.get_field(CooldownFields.expires_at)
                message_dict["cooldown_end"] = cooldown_end
            # Get Team info
            team_players = await database.table_team_player.get_team_player_records(
                player_id=player_id
            )
            team_player = team_players[0] if team_players else None
            if team_player:
                team_id = await team_player.get_field(TeamPlayerFields.team_id)
                teams = await database.table_team.get_team_records(record_id=team_id)
                assert teams, "Player team not found"
                team = teams[0] if teams else None
                team_name = await team.get_field(TeamFields.team_name)
                is_captain = await team_player.get_field(TeamPlayerFields.is_captain)
                is_co_cap = await team_player.get_field(TeamPlayerFields.is_co_captain)
                message_dict["team"] = team_name
                team_role = "member"
                team_role = "captain" if is_captain else team_role
                team_role = "co-captain" if is_co_cap else team_role
                message_dict["team_role"] = team_role
            message_data.append(message_dict)
        # Create Response
        if len(message_data) == 1:
            message_data = message_data[0]
        message = await general_helpers.format_json(message_data)
        message = await discord_helpers.code_block(message, language="json")
        return await discord_helpers.final_message(interaction, message)
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
