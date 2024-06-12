from database.database_full import FullDatabase
from database.fields import PlayerFields, TeamFields, TeamPlayerFields, SuspensionFields
from utils import discord_helpers, database_helpers, general_helpers
import discord
import constants


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
        # "My" Suspension
        my_suspension_records = await database.table_suspension.get_suspension_records(
            player_id=interaction.user.id
        )
        assert (
            not my_suspension_records
        ), f"You are suspended until `{await my_suspension_records[0].get_field(SuspensionFields.expires_at)}`."
        # "My" Player
        my_players = await database.table_player.get_player_records(
            discord_id=interaction.user.id
        )
        assert my_players, "You must be registered as a player to create a team."
        my_player = my_players[0]
        # "My" TeamPlayer
        my_teamplayers = await database.table_team_player.get_team_player_records(
            player_id=await my_player.get_field(PlayerFields.record_id)
        )
        assert not my_teamplayers, "You are already a member of a team."

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################

        # Create Team
        ok_chars = set(constants.INPUT_ALLOWED_CHARS_TEAM_NAME)
        special_chars = constants.INPUT_ALLOWED_CHARS_LIMITED
        clean_name = "".join([char for char in team_name if char in ok_chars])
        clean_name = ""
        for char_a in team_name:
            for char_b in ok_chars:
                if char_a == char_b:
                    clean_name += char_b
        assert (
            clean_name == team_name
        ), f"Team name contains invalid characters. Only the following characters are allowed: [`{constants.INPUT_ALLOWED_CHARS_TEAM_NAME}`]"
        assert (
            len(team_name) >= 3 and len(team_name) <= 32
        ), "Team name must be between 3 and 32 characters long."
        for i in range(len(team_name) - 1):
            a = team_name[i] in set(special_chars)
            b = team_name[i + 1] in set(special_chars)
            assert not (
                a and b
            ), f"Team name must not contain consecutive special characters: [`{constants.INPUT_ALLOWED_CHARS_LIMITED}`]"
        assert team_name[0] not in set(special_chars) and team_name[-1] not in set(
            special_chars
        ), f"Team name must not start or end with a special character: [`{constants.INPUT_ALLOWED_CHARS_LIMITED}`]"
        new_team_record = await database.table_team.create_team_record(
            team_name=team_name,
            vw_region=await my_player.get_field(PlayerFields.region),
        )
        assert new_team_record, "Error: Failed to create team."
        # Create TeamPlayer
        new_teamplayer_record = (
            await database.table_team_player.create_team_player_record(
                team_id=await new_team_record.get_field(TeamFields.record_id),
                team_name=await new_team_record.get_field(TeamFields.team_name),
                player_id=await my_player.get_field(PlayerFields.record_id),
                player_name=await my_player.get_field(PlayerFields.player_name),
                is_captain=True,
            )
        )
        assert new_teamplayer_record, "Error: Failed to add captain to new team."

        # Add Discord roles
        await discord_helpers.add_member_to_team(
            member=interaction.user,
            team_name=await new_team_record.get_field(TeamFields.team_name),
        )
        await discord_helpers.member_add_captain_role(
            member=interaction.user,
            region=await my_player.get_field(PlayerFields.region),
        )

        # Update roster view
        await database_helpers.update_roster_view(
            database=database,
            team_name=await new_team_record.get_field(TeamFields.team_name),
        )

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        team_name = f"{await new_teamplayer_record.get_field(TeamPlayerFields.vw_team)}"
        response_dictionary = {
            "team_name": f"{await new_teamplayer_record.get_field(TeamPlayerFields.vw_team)}",
            "is_active": f"{await new_team_record.get_field(TeamFields.status)}",
            "captain": f"{await new_teamplayer_record.get_field(TeamPlayerFields.vw_player)}",
            "co-captain": None,
            "players": [],
        }
        response_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(response_dictionary), "json"
        )
        await discord_helpers.final_message(
            interaction=interaction,
            message="\n".join(
                [
                    f"Team created: `{team_name}`.",
                    f"{response_code_block}",
                ]
            ),
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################
        team_name = await new_teamplayer_record.get_field(TeamPlayerFields.vw_team)
        my_player_mention = f"{await discord_helpers.role_mention(guild=interaction.guild, discord_id=await new_teamplayer_record.get_field(TeamPlayerFields.player_id))}"
        await discord_helpers.log_to_channel(
            interaction=interaction,
            message=f"`{team_name}` has been created by {my_player_mention}",
        )

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
