from bot_dialogues import choices
from database.database_full import FullDatabase
from database.enums import Regions
from utils import discord_helpers, player_helpers
import discord


async def player_register(
    database: FullDatabase,
    interaction: discord.Interaction,
    region: str = None,
):
    """Register a new Player"""
    try:
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
        # Get region
        options_dict = {
            Regions.EU.value: "Europe",
            Regions.NA.value: "North America",
            Regions.OCE.value: "Oceania",
        }
        view = choices.QuestionPromptView(options_dict=options_dict)
        await interaction.response.send_message(
            content="Choose a region", view=view, ephemeral=True
        )
        await view.wait()
        region = view.value
        # Get player info
        discord_id = interaction.user.id
        player_name = interaction.user.display_name
        allowed_regions = [r.value for r in Regions]
        region = await player_helpers.normalize_region(region)
        assert region, f"Region must be in {allowed_regions}"
        # Check for existing Players with the same DisplayName or Discord ID
        existing_players = await database.table_player.get_player_records(
            discord_id=discord_id
        )
        assert not existing_players, "You are already registered."
        existing_players = await database.table_player.get_player_records(
            player_name=player_name
        )
        assert not existing_players, f"Player name {player_name} already in use."
        # Create Player record
        await database.table_player.create_player_record(
            discord_id=discord_id, player_name=player_name, region=region
        )
        # Add Player role
        await player_helpers.member_add_player_role(interaction.user, region=region)
        # Success
        message = f"Player '{player_name}' registered for region '{region}'"
        await discord_helpers.final_message(interaction, message)
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"{interaction.user.mention} has joined the League.",
        )
    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
