from database.database_full import FullDatabase
from database.fields import PlayerFields
from utils import discord_helpers, database_helpers
import discord


async def team_create(
    database: FullDatabase,
    interaction: discord.Interaction,
    team_name: str,
):
    """Create a Team with the given name

    Process:
    - Check if the Player is registered
    - Create the Team and Captain Database Records
    - Update Discord roles
    """
    try:
        await interaction.response.defer()
        #######################################################################
        #                               RECORDS                               #
        #######################################################################
        #######################################################################
        #                               OPTIONS                               #
        #######################################################################
        #######################################################################
        #                               CHOICE                                #
        #######################################################################
        #######################################################################
        #                             PROCESSING                              #
        #######################################################################
        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        #######################################################################
        #                               LOGGING                               #
        #######################################################################
        allowed_chars = ""
        allowed_chars += "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        allowed_chars += "abcdefghijklmnopqrstuvwxyz"
        allowed_chars += "0123456789"
        allowed_chars += "-_ "
        filtered_team_name = "".join(
            [char for char in team_name if char in set(allowed_chars)]
        )
        assert (
            filtered_team_name == team_name
        ), f"Team name contains invalid characters. Only the following characters are allowed: [`{allowed_chars}`]"
        assert len(team_name) >= 3, f"Team name must be at least 3 characters long."
        assert len(team_name) <= 32, f"Team name must be under 32 characters long."
        # Check if the Player is registered
        discord_id = interaction.user.id
        players = await database.table_player.get_player_records(discord_id=discord_id)
        assert players, f"You must be registered as a player to create a team."
        player = players[0]
        # Create Team and Captain Database Records
        player_id = await player.get_field(PlayerFields.record_id)
        new_team = await database_helpers.create_team(database, player_id, team_name)
        # Update Discord roles
        discord_member = interaction.user
        region = await player.get_field(PlayerFields.region)
        await discord_helpers.add_member_to_team(discord_member, team_name)
        await discord_helpers.member_add_captain_role(discord_member, region)
        # Update roster view
        await database_helpers.update_roster_view(database, team_name=team_name)
        # Success
        user_message = f"Team created: '{team_name}'"
        await discord_helpers.final_message(interaction, user_message)
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"`{team_name}` has been created by {discord_member.mention}",
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
