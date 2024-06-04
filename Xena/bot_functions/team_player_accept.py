from bot_dialogues import choices
from database.database_full import FullDatabase
from database.enums import InviteStatus
from database.fields import TeamInviteFields, PlayerFields, TeamFields
from utils import discord_helpers, database_helpers
import discord


async def team_player_accept(
    database: FullDatabase,
    interaction: discord.Interaction,
    log_channel: discord.TextChannel = None,
):
    """Add the requestor to their new Team"""
    try:
        # Get info about the Player
        players = await database.table_player.get_player_records(
            discord_id=interaction.user.id
        )
        assert players, f"You must be registered as a Player to accept an invite."
        player = players[0]
        player_id = await player.get_field(PlayerFields.record_id)
        # Gather Invites
        invites = await database.table_team_invite.get_team_invite_records(
            to_player_id=player_id
        )
        assert invites, f"No invites found."
        # Gather Team options
        options_dict = {}
        all_teams = await database.table_team.get_table_data()
        for invite in invites:
            team_id = await invite.get_field(TeamInviteFields.from_team_id)
            for team in all_teams:
                if team[TeamFields.record_id] == team_id:
                    team_name = team[TeamFields.team_name]
                    options_dict[team_id] = team_name
        # Create the view to display the options
        view = choices.QuestionPromptView(
            options_dict=options_dict,
            initial_button_style=discord.ButtonStyle.success,
        )
        # Add option to clear invites
        clearall_button = choices.QuestionOptionButton(
            label="Decline All",
            style=discord.ButtonStyle.danger,
            custom_id="clearall",
        )
        view.add_item(clearall_button)
        # Add option to cancel without making a choice
        cancel_button = choices.QuestionOptionButton(
            label="Cancel",
            style=discord.ButtonStyle.primary,
            custom_id="cancel",
        )
        view.add_item(cancel_button)
        # Send the message with the options
        await interaction.response.send_message(
            content="Choose a team", view=view, ephemeral=True
        )
        # Wait for the user to make a choice
        await view.wait()
        # Process the user's choice
        choice = view.value
        if not choice or choice == "cancel":
            return await interaction.followup.send("No team selected.")
        # clear invites
        for invite in invites:
            if await invite.get_field(TeamInviteFields.from_team_id) != choice:
                await invite.set_field(
                    TeamInviteFields.invite_status, InviteStatus.DECLINED
                )
            else:
                await invite.set_field(
                    TeamInviteFields.invite_status, InviteStatus.ACCEPTED
                )
            await database.table_team_invite.update_team_invite_record(invite)
            await database.table_team_invite.delete_team_invite_record(invite)
        if choice == "clearall":
            # We are done here if no team was selected
            return await interaction.followup.send("Invites cleared.")
        # Add player to the team
        team_id = choice
        team_name = options_dict[team_id]
        await database_helpers.add_player_to_team(database, player_id, team_name)
        await discord_helpers.add_member_to_team(interaction.user, team_name)
        # Update roster view
        await database_helpers.update_roster_view(database, team_id)
        # Success
        message = f"You have joined Team '{team_name}'"
        await discord_helpers.final_message(interaction, message)
        team_role = await discord_helpers.get_team_role(
            guild=interaction.guild, team_name=team_name
        )
        await discord_helpers.log_to_channel(
            channel=log_channel,
            message=f"{interaction.user.mention} has joined {team_role.mention}",
        )
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
