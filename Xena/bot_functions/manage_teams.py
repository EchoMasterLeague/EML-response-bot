from bot_dialogues import choices
from database.database_full import FullDatabase
from database.enums import InviteStatus
from database.fields import TeamInviteFields, PlayerFields, TeamPlayerFields, TeamFields
from database.records import TeamRecord, PlayerRecord
from utils import discord_helpers, database_helpers, general_helpers
import constants
import datetime
import discord


class ManageTeams:
    """EML Team Management"""

    def __init__(self, database: FullDatabase):
        self._db = database

    async def create_team(
        self,
        interaction: discord.Interaction,
        team_name: str,
        log_channel: discord.TextChannel = None,
    ):
        """Create a Team with the given name

        Process:
        - Check if the Player is registered
        - Create the Team and Captain Database Records
        - Update Discord roles
        """
        try:
            # This could take a while
            await interaction.response.defer()
            # Check if the Player is registered
            discord_id = interaction.user.id
            player = await self._db.table_player.get_player_record(
                discord_id=discord_id
            )
            assert player, f"You must be registered as a player to create a team."
            # Create Team and Captain Database Records
            player_id = await player.get_field(PlayerFields.record_id)
            new_team = await database_helpers.create_team(
                self._db, player_id, team_name
            )
            # Update Discord roles
            discord_member = interaction.user
            region = await player.get_field(PlayerFields.region)
            await discord_helpers.add_member_to_team(discord_member, team_name)
            await discord_helpers.member_add_captain_role(discord_member, region)
            # Update roster view
            await database_helpers.update_roster_view(self._db, team_name=team_name)
            # Success
            user_message = f"Team created: '{team_name}'"
            await discord_helpers.final_message(interaction, user_message)
            await discord_helpers.log_to_channel(
                log_channel,
                f"`{team_name}` has been created by {discord_member.mention}",
            )
        except AssertionError as message:
            await discord_helpers.final_message(interaction, message)
        except Exception as error:
            await discord_helpers.error_message(interaction, error)

    async def invite_player_to_team(
        self, interaction: discord.Interaction, player_name
    ):
        """Invite a Player to a Team by name"""
        try:
            # This could take a while
            await interaction.response.defer()
            # Get Player Record for inviter
            inviter = await self._db.table_player.get_player_record(
                discord_id=interaction.user.id
            )
            assert_message = f"You must be registered as a player to invite players."
            assert inviter, assert_message
            # check permissions
            team_details = await database_helpers.get_team_details_from_player(
                self._db, inviter, assert_captain=True
            )
            assert team_details, f"You must be a captain to invite players."
            # Get player record for invitee
            invitee = await self._db.table_player.get_player_record(
                player_name=player_name
            )
            assert_message = f"Player `{player_name}` not found. Please check the spelling, and verify the player is registered."
            assert invitee, assert_message
            # Create Invite record
            new_invite = await database_helpers.create_team_invite(
                self._db, inviter, invitee
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

    async def accept_invite(
        self, interaction: discord.Interaction, log_channel: discord.TextChannel = None
    ):
        """Add the requestor to their new Team"""
        try:
            # Get info about the Player
            player = await self._db.table_player.get_player_record(
                discord_id=interaction.user.id
            )
            assert player, f"You must be registered as a Player to accept an invite."
            player_id = await player.get_field(PlayerFields.record_id)
            # Gather Invites
            invites = await self._db.table_team_invite.get_team_invite_records(
                to_player_id=player_id
            )
            assert invites, f"No invites found."
            # Gather Team options
            options_dict = {}
            all_teams = await self._db.table_team.get_table_data()
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
                await self._db.table_team_invite.update_team_invite_record(invite)
                await self._db.table_team_invite.delete_team_invite_record(invite)
            if choice == "clearall":
                # We are done here if no team was selected
                return await interaction.followup.send("Invites cleared.")
            # Add player to the team
            team_id = choice
            team_name = options_dict[team_id]
            await database_helpers.add_player_to_team(self._db, player_id, team_name)
            await discord_helpers.add_member_to_team(interaction.user, team_name)
            # Update roster view
            await database_helpers.update_roster_view(self._db, team_id)
            # Success
            message = f"You have joined Team '{team_name}'"
            await discord_helpers.final_message(interaction, message)
            team_role = await discord_helpers.get_team_role(
                guild=interaction.guild, team_name=team_name
            )
            await discord_helpers.log_to_channel(
                log_channel=log_channel,
                message=f"{interaction.user.mention} has joined {team_role.mention}",
            )
        except AssertionError as message:
            await discord_helpers.final_message(interaction, message)
        except Exception as error:
            await discord_helpers.error_message(interaction, error)

    async def remove_player_from_team(
        self,
        interaction: discord.Interaction,
        player_name: str,
        log_channel: discord.TextChannel = None,
    ):
        """Remove a Player from a Team by name"""
        try:
            # This could take a while
            await interaction.response.defer()
            # Get requestor's Team Details
            requestor = await self._db.table_player.get_player_record(
                discord_id=interaction.user.id
            )
            assert_message = f"You register as a player, and be cpatin of a team to remove players from it."
            assert requestor, assert_message
            team_details = await database_helpers.get_team_details_from_player(
                self._db, requestor, assert_captain=True
            )
            assert (
                team_details
            ), f"You must be the captain of a team to remove players from it."
            # Verify Player exists
            player = await self._db.table_player.get_player_record(
                player_name=player_name
            )
            player_name = await player.get_field(PlayerFields.player_name)
            assert_message = f"Player `{player_name}` not found. Please check the spelling, and verify the player is registered."
            assert player, assert_message
            # Remove Player from Team
            player_id = await player.get_field(PlayerFields.record_id)
            team_id = await team_details.team.get_field(TeamFields.record_id)
            await database_helpers.remove_player_from_team(self._db, player_id, team_id)
            # Update Player's Discord roles
            player_discord_member = await discord_helpers.member_from_discord_id(
                guild=interaction.guild,
                discord_id=await player.get_field(PlayerFields.discord_id),
            )
            await discord_helpers.member_remove_team_roles(player_discord_member)
            # Update roster view
            await database_helpers.update_roster_view(self._db, team_id)
            # Success
            team_name = await team_details.team.get_field(TeamFields.team_name)
            message = f"Player `{player_name}` removed from team `{team_name}`."
            await discord_helpers.final_message(interaction, message)
            team_role = await discord_helpers.get_team_role(
                guild=interaction.guild, team_name=team_name
            )
            await discord_helpers.log_to_channel(
                channel=log_channel,
                message=f"{player_discord_member.mention} has been removed from {team_role.mention}",
            )
        except AssertionError as message:
            await discord_helpers.final_message(interaction, message)
        except Exception as error:
            await discord_helpers.error_message(interaction, error)

    async def promote_player_to_co_captain(
        self,
        interaction: discord.Interaction,
        player_name: str,
        log_channel: discord.TextChannel = None,
    ):
        """Promote a Player to Team captain"""
        try:
            # This could take a while
            await interaction.response.defer()
            # Get info about the requestor
            requestor = await self._db.table_player.get_player_record(
                discord_id=interaction.user.id
            )
            assert requestor, f"You must be registered as a player to promote players."
            requestor_id = await requestor.get_field(PlayerFields.record_id)
            requestor_team_players = (
                await self._db.table_team_player.get_team_player_records(
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
            team_players = await self._db.table_team_player.get_team_player_records(
                team_id=team_id
            )
            # Get info about co-captain
            co_captain_id = None
            for team_player in team_players:
                if await team_player.get_field(TeamPlayerFields.is_co_captain):
                    co_captain_id = await team_player.get_field(
                        TeamPlayerFields.player_id
                    )
            assert not co_captain_id, f"Team already has a co-captain."
            # Get info about the Player
            player = await self._db.table_player.get_player_record(
                player_name=player_name
            )
            assert player, f"Player not found."
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
            await self._db.table_team_player.update_team_player_record(
                player_team_player
            )
            # Update Player's Discord roles
            region = await requestor.get_field(PlayerFields.region)
            player_discord_id = await player.get_field(PlayerFields.discord_id)
            player_discord_member = await discord_helpers.member_from_discord_id(
                guild=interaction.guild,
                discord_id=player_discord_id,
            )
            await discord_helpers.member_add_co_captain_role(
                player_discord_member, region
            )
            new_role_names = [role.name for role in player_discord_member.roles]
            # Update roster view
            await database_helpers.update_roster_view(self._db, team_id)
            # Success
            message = f"Player '{player_name}' promoted to co-captain"
            await discord_helpers.final_message(interaction, message)
            cocap = constants.ROLE_PREFIX_CO_CAPTAIN
            cocap_roles = [role for role in new_role_names if role.startswith(cocap)]
            cocap_role = next(cocap_roles, None)
            await discord_helpers.log_to_channel(
                channel=log_channel,
                message=f"{player_discord_member.mention} has new role `{cocap_role}`",
            )
        except AssertionError as message:
            await discord_helpers.final_message(interaction, message)
        except Exception as error:
            await discord_helpers.error_message(interaction, error)

    async def demote_player_from_co_captain(
        self,
        interaction: discord.Interaction,
        player_name: str,
        log_channel: discord.TextChannel = None,
    ):
        """Demote a Player from Team captain"""
        try:
            # This could take a while
            await interaction.response.defer()
            # Get info about the requestor
            requestor = await self._db.table_player.get_player_record(
                discord_id=interaction.user.id
            )
            assert requestor, f"You must be registered as a player to demote players."
            requestor_id = await requestor.get_field(PlayerFields.record_id)
            requestor_team_players = (
                await self._db.table_team_player.get_team_player_records(
                    player_id=requestor_id
                )
            )
            assert requestor_team_players, f"You must be on a team to demote players."
            requestor_team_player = requestor_team_players[0]
            requestor_is_captain = await requestor_team_player.get_field(
                TeamPlayerFields.is_captain
            )
            assert requestor_is_captain, f"You must be team captain to demote players."
            # Get info about the Team
            team_id = await requestor_team_player.get_field(TeamPlayerFields.team_id)
            team_players = await self._db.table_team_player.get_team_player_records(
                team_id=team_id
            )
            # Get info about the Player
            player = await self._db.table_player.get_player_record(
                player_name=player_name
            )
            assert player, f"Player not found."
            player_name = await player.get_field(PlayerFields.player_name)
            player_id = await player.get_field(PlayerFields.record_id)
            player_team_player = None
            for team_player in team_players:
                if await team_player.get_field(TeamPlayerFields.player_id) == player_id:
                    player_team_player = team_player
            assert player_team_player, f"Player is not on the team."
            is_co_captain = await player_team_player.get_field(
                TeamPlayerFields.is_co_captain
            )
            assert is_co_captain, f"Player is not a co-captain."
            # Update Player's TeamPlayer record
            await player_team_player.set_field(TeamPlayerFields.is_co_captain, False)
            await self._db.table_team_player.update_team_player_record(
                player_team_player
            )
            # Update Player's Discord roles
            player_discord_id = await player.get_field(PlayerFields.discord_id)
            player_discord_member = await discord_helpers.member_from_discord_id(
                guild=interaction.guild,
                discord_id=player_discord_id,
            )
            old_role_names = [role.name for role in player_discord_member.roles]
            await discord_helpers.member_remove_captain_roles(player_discord_member)
            # Update roster view
            await database_helpers.update_roster_view(self._db, team_id)
            # Success
            message = f"Player '{player_name}' demoted from co-captain"
            await discord_helpers.final_message(interaction, message)
            cocap = constants.ROLE_PREFIX_CO_CAPTAIN
            cocap_roles = [role for role in old_role_names if role.startswith(cocap)]
            cocap_role = next(cocap_roles, None)
            await discord_helpers.log_to_channel(
                channel=log_channel,
                message=f"{player_discord_member.mention} has lost role `{cocap_role}`",
            )
        except AssertionError as message:
            await discord_helpers.final_message(interaction, message)
        except Exception as error:
            await discord_helpers.error_message(interaction, error)

    async def leave_team(
        self, interaction: discord.Interaction, log_channel: discord.TextChannel = None
    ):
        """Remove the requestor from their Team"""
        try:
            # This could take a while
            await interaction.response.defer()
            # Get info about the requestor
            requestor = await self._db.table_player.get_player_record(
                discord_id=interaction.user.id
            )
            assert requestor, f"You must be registered as a Player to leave a Team."
            requestor_player_id = await requestor.get_field(PlayerFields.record_id)
            requestor_team_players = (
                await self._db.table_team_player.get_team_player_records(
                    player_id=requestor_player_id
                )
            )
            assert requestor_team_players, f"You must be on a team to leave."
            requestor_team_player = requestor_team_players[0]
            requestor_is_captain = await requestor_team_player.get_field(
                TeamPlayerFields.is_captain
            )
            # Get info about the Team
            team_id = await requestor_team_player.get_field(TeamPlayerFields.team_id)
            team = await self._db.table_team.get_team_record(record_id=team_id)
            team_name = await team.get_field(TeamFields.team_name)
            team_players = await self._db.table_team_player.get_team_player_records(
                team_id=team_id
            )
            if requestor_is_captain:
                # Get info about the co-captain
                co_captain_team_player = None
                for team_player in team_players:
                    if await team_player.get_field(TeamPlayerFields.is_co_captain):
                        co_captain_team_player = team_player
                assert (
                    co_captain_team_player
                ), f"Captain must promote a co-captain before leaving."
                # promote the co-captain to captain
                co_cap = co_captain_team_player
                await co_cap.set_field(TeamPlayerFields.is_captain, True)
                await co_cap.set_field(TeamPlayerFields.is_co_captain, False)
                await self._db.table_team_player.update_team_player_record(co_cap)
            # Apply cooldown
            player_name = await requestor.get_field(PlayerFields.player_name)
            new_cooldown = await self._db.table_cooldown.create_cooldown_record(
                player_id=requestor_player_id,
                old_team_id=team_id,
                player_name=player_name,
                old_team_name=team_name,
            )
            assert new_cooldown, f"Error: Could not apply cooldown."
            # Remove the Player from the Team
            await self._db.table_team_player.delete_team_player_record(
                requestor_team_player
            )
            # Update Player's Discord roles
            member = interaction.user
            await discord_helpers.member_remove_team_roles(member)
            # Update roster view
            await database_helpers.update_roster_view(self._db, team_id)
            # Success
            message = f"You have left Team '{team_name}'"
            await discord_helpers.final_message(interaction, message)
            team_role = await discord_helpers.get_team_role(
                guild=interaction.guild, team_name=team_name
            )
            await discord_helpers.log_to_channel(
                channel=log_channel,
                message=f"{member.mention} has left {team_role.mention}",
            )
        except AssertionError as message:
            await discord_helpers.final_message(interaction, message)
        except Exception as error:
            await discord_helpers.error_message(interaction, error)

    async def disband_team(
        self, interaction: discord.Interaction, log_channel: discord.TextChannel = None
    ):
        """Disband the requestor's Team"""
        try:
            # This could take a while
            await interaction.response.defer()
            # Get info about the requestor
            requestor = await self._db.table_player.get_player_record(
                discord_id=interaction.user.id
            )
            assert requestor, f"You must be registered as a player to disband a team."
            requestor_id = await requestor.get_field(PlayerFields.record_id)
            requestor_team_players = (
                await self._db.table_team_player.get_team_player_records(
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
            team = await self._db.table_team.get_team_record(record_id=team_id)
            team_name = await team.get_field(TeamFields.team_name)
            team_players = await self._db.table_team_player.get_team_player_records(
                team_id=team_id
            )
            # Remove all Players from the Team
            discord_members: list[discord.Member] = []
            for team_player in team_players:
                # Remove Player's Discord roles
                player_id = await team_player.get_field(TeamPlayerFields.player_id)
                player = await self._db.table_player.get_player_record(
                    record_id=player_id
                )
                player_discord_id = await player.get_field(PlayerFields.discord_id)
                player_discord_member = await discord_helpers.member_from_discord_id(
                    guild=interaction.guild,
                    discord_id=player_discord_id,
                )
                discord_members.append(player_discord_member)
                await discord_helpers.member_remove_team_roles(player_discord_member)
                # Apply cooldown
                player_name = await player.get_field(PlayerFields.player_name)
                new_cooldown = await self._db.table_cooldown.create_cooldown_record(
                    player_id=player_id,
                    old_team_id=team_id,
                    player_name=player_name,
                    old_team_name=team_name,
                )
                assert new_cooldown, f"Error: Could not apply cooldown."
                # Remove the Player from the Team
                await self._db.table_team_player.delete_team_player_record(team_player)
            # Delete the Team
            await self._db.table_team.delete_team_record(team)
            await discord_helpers.guild_remove_team_role(interaction.guild, team_name)
            # Update roster view
            await database_helpers.update_roster_view(self._db, team_id)
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

    async def get_team_details(
        self, interaction: discord.Interaction, team_name: str = None
    ):
        """Get a Team by name"""
        try:
            # This could take a while
            await interaction.response.defer()
            # Determine desired team
            team = None
            if not team_name:
                requestor = await self._db.table_player.get_player_record(
                    discord_id=interaction.user.id
                )
                requestor_id = await requestor.get_field(PlayerFields.record_id)
                team_players = await self._db.table_team_player.get_team_player_records(
                    player_id=requestor_id
                )
                assert team_players, f"No team specified."
                team_player = team_players[0]
                team_id = await team_player.get_field(TeamPlayerFields.team_id)
                team = await self._db.table_team.get_team_record(record_id=team_id)
            # Get info about the Team
            if not team:
                team = await self._db.table_team.get_team_record(team_name=team_name)
            assert team, f"Team not found."
            team_name = await team.get_field(TeamFields.team_name)
            team_id = await team.get_field(TeamFields.record_id)
            team_players = await self._db.table_team_player.get_team_player_records(
                team_id=team_id
            )
            # Get info about the Players
            captain_name = None
            co_captain_name = None
            player_names = []
            for team_player in team_players:
                player_id = await team_player.get_field(TeamPlayerFields.player_id)
                player = await self._db.table_player.get_player_record(
                    record_id=player_id
                )
                player_name = await player.get_field(PlayerFields.player_name)
                player_names.append(player_name)
                if await team_player.get_field(TeamPlayerFields.is_captain):
                    captain_name = player_name
                elif await team_player.get_field(TeamPlayerFields.is_co_captain):
                    co_captain_name = player_name
            player_names.sort()
            # Format the message
            message_dict = {
                "team": team_name,
                "captain": captain_name,
                "co_captain": co_captain_name,
                "players": player_names,
            }
            message = await general_helpers.format_json(message_dict)
            message = await discord_helpers.code_block(message, language="json")
            return await discord_helpers.final_message(interaction, message)
        except AssertionError as message:
            await discord_helpers.final_message(interaction, message)
        except Exception as error:
            await discord_helpers.error_message(interaction, error)
