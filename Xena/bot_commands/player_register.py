from bot_dialogues import choices
from database.database_full import FullDatabase
from database.enums import Regions
from database.fields import PlayerFields, SuspensionFields
from utils import discord_helpers, player_helpers, general_helpers
import constants
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
        # "My" Suspension
        my_suspension_records = await database.table_suspension.get_suspension_records(
            player_id=interaction.user.id
        )
        assert (
            not my_suspension_records
        ), f"You are suspended until `{await my_suspension_records[0].get_field(SuspensionFields.expires_at)}`."
        # "My" Player
        my_player_records = await database.table_player.get_player_records(
            discord_id=interaction.user.id
        )
        assert not my_player_records, "You are already registered."
        my_player_records = await database.table_player.get_player_records(
            player_name=interaction.user.display_name
        )
        assert (
            not my_player_records
        ), f"Player name `{interaction.user.display_name}` already in use."
        #######################################################################
        #                               OPTIONS                               #
        #######################################################################
        # Get Options
        options_dict = {
            Regions.EU.value: "Europe",
            Regions.NA.value: "North America",
            Regions.OCE.value: "Oceania",
        }
        # Options View
        options_view = choices.QuestionPromptView(
            options_dict=options_dict,
            initial_button_style=discord.ButtonStyle.success,
        )
        # Button: Cancel
        options_view.add_item(
            choices.QuestionOptionButton(
                label="Cancel",
                style=discord.ButtonStyle.primary,
                custom_id="cancel",
            )
        )
        # Show Options
        await interaction.response.send_message(
            view=options_view,
            content="\n".join(
                [
                    f"Choose a region",
                ]
            ),
            ephemeral=True,
        )
        #######################################################################
        #                               CHOICE                                #
        #######################################################################
        # Wait for Choice
        await options_view.wait()
        # Get Choice
        choice = options_view.value
        # Choice: Cancel (default)
        if not choice or choice == "cancel":
            return await discord_helpers.final_message(
                interaction=interaction, message=f"No region selected."
            )
        # Choice: [Region]
        selected_region = None
        for region in Regions:
            if choice == region.value:
                selected_region = region
                break
        assert selected_region, f"Region not found."

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################

        # Normalize Region
        region = await player_helpers.normalize_region(selected_region)
        assert region, f"Region must be in {[r.value for r in Regions]}"

        # Create Player record
        user_name = interaction.user.display_name
        ok_chars = set(constants.INPUT_ALLOWED_CHARS_TEAM_NAME)
        special_chars = constants.INPUT_ALLOWED_CHARS_LIMITED
        clean_name = "".join([char for char in user_name if char in ok_chars])
        clean_name = ""
        for char_a in user_name:
            for char_b in ok_chars:
                if char_a == char_b:
                    clean_name += char_b
        assert (
            clean_name == user_name
        ), f"Player name contains invalid characters. Only the following characters are allowed: [`{constants.INPUT_ALLOWED_CHARS_PLAYER_NAME}`]"
        assert (
            len(user_name) >= 3 and len(user_name) <= 32
        ), "Player name must be between 3 and 32 characters long."
        for i in range(len(user_name) - 1):
            a = user_name[i] in set(special_chars)
            b = user_name[i + 1] in set(special_chars)
            assert not (
                a and b
            ), f"Player name must not contain consecutive special characters: [`{constants.INPUT_ALLOWED_CHARS_LIMITED}`]"
        new_player_record = await database.table_player.create_player_record(
            discord_id=interaction.user.id,
            player_name=interaction.user.display_name,
            region=region,
        )

        # Add Player role
        await player_helpers.member_add_player_role(interaction.user, region=region)

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        player_name = await new_player_record.get_field(PlayerFields.player_name)
        region = await new_player_record.get_field(PlayerFields.region)
        response_dictionary = {
            "player": f"{await new_player_record.get_field(PlayerFields.player_name)}",
            "region": f"{await new_player_record.get_field(PlayerFields.region)}",
            "team": None,
            "team_role": None,
        }
        response_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(response_dictionary), "json"
        )
        await discord_helpers.final_message(
            interaction=interaction,
            message="\n".join(
                [
                    f"Player `{player_name}` registered for region `{region}`:",
                    f"{response_code_block}",
                ]
            ),
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################
        my_player_mention = f"{await discord_helpers.role_mention(guild=interaction.guild, discord_id=await new_player_record.get_field(PlayerFields.discord_id))}"
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"{my_player_mention} has joined the League.",
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
