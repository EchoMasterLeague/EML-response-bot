from database.database_full import FullDatabase
from utils import discord_helpers, database_helpers, general_helpers
import discord


async def team_player_invite(
    database: FullDatabase,
    interaction: discord.Interaction,
    player_name: str = None,
    player_discord_id: str = None,
):
    """Invite a Player to a Team by name"""
    try:
        # This could take a while
        await interaction.response.defer()
        # Get Player Record for inviter
        inviter_matches = await database.table_player.get_player_records(
            discord_id=interaction.user.id
        )
        assert inviter_matches, f"You must be registered as a player to invite players."
        inviter = inviter_matches[0]
        # check permissions
        team_details = await database_helpers.get_team_details_from_player(
            database, inviter, assert_captain=True
        )
        assert team_details, f"You must be a captain to invite players."
        # Get player record for invitee
        assert player_name or player_discord_id, f"Please specify a player to invite."
        invitee_matches = await database.table_player.get_player_records(
            player_name=player_name, discord_id=player_discord_id
        )
        assert (
            invitee_matches
        ), f"Player not found. Please verify the player is registered."
        assert (
            len(invitee_matches) == 1
        ), f"Multiple players found. Please specify the player's Discord ID (nubmers only) to invite them."
        invitee = invitee_matches[0]
        # Create Invite record
        new_invite = await database_helpers.create_team_invite(
            database, inviter, invitee
        )
        # Success
        new_invite_dict = await new_invite.to_dict()
        new_invite_json = await general_helpers.format_json(new_invite_dict)
        new_invite_block = await discord_helpers.code_block(new_invite_json, "json")
        message = f"Team invite sent.\n{new_invite_block}"
        return await discord_helpers.final_message(interaction, message)
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
