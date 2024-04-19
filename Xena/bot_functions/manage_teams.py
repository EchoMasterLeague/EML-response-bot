import utils.general_helpers as bot_helpers
from utils import discord_helpers
from database.related_records import RelatedRecords
from database.database import Database
import constants
import discord
import errors.database_errors as DbErrors
from database.table_player import PlayerFields, PlayerRecord, PlayerTable
from database.table_team import TeamFields, TeamRecord, TeamTable
from database.table_team_player import (
    TeamPlayerFields,
    TeamPlayerRecord,
    TeamPlayerTable,
)


class ManageTeams:
    """EML Team Management"""

    def __init__(self, database: Database):
        self.database = database
        self.related_records = RelatedRecords(database)
        self.table_team = TeamTable(database)
        self.table_player = PlayerTable(database)
        self.table_team_player = TeamPlayerTable(database)

    async def register_team(self, interaction: discord.Interaction, team_name: str):
        """Create a Team with the given name

        Process:
        - Check if the Player is registered
        - Check if the Player is already on a Team
        - Check if the Team already exists
        - Create the Team and Captain Database Records
        - Update Discord roles
        """
        try:
            # This could take a while
            await interaction.response.defer()
            # Check if the Player is registered
            discord_id = interaction.user.id
            player = await self.table_player.get_player_record(discord_id=discord_id)
            if not player:
                message = f"You must be registered as a player to create a Team."
                return await interaction.followup.send(message)
            # Check if the Player is already on a Team
            existing_team = await self.related_records.get_team_from_player(player)
            if existing_team:
                existing_team_name = await existing_team.get_field(TeamFields.team_name)
                message = f"You are already on a Team: {existing_team_name}"
                return await interaction.followup.send(message)
            # Check if the Team already exists
            existing_team = await self.table_team.get_team_record(team_name=team_name)
            if existing_team:
                message = f"Team already exists: {team_name}"
                return await interaction.followup.send(message)
            # Create the Team and Captain Records
            try:
                new_team = await self.related_records.create_new_team_with_captain(
                    team_name=team_name, player=player
                )
            except DbErrors.EmlRecordNotInserted:
                message = f"Error: Failed to create Team: {team_name}"
                return await interaction.followup.send(message)
            team_id = await new_team.get_field(TeamFields.record_id)
            player_id = await player.get_field(PlayerFields.record_id)
            team_players = await self.table_team_player.get_team_player_records(
                team_id=team_id, player_id=player_id
            )
            team_player = team_players[0] if team_players else None
            if not team_player:
                message = f"Error: Failed to add Captain: {team_name}"
                return await interaction.followup.send(message)
            # Update Discord roles
            member = interaction.user
            region = await player.get_field(PlayerFields.region)
            await ManageTeamsHelpers.member_remove_team_roles(member)
            await ManageTeamsHelpers.member_add_team_role(member, team_name)
            await ManageTeamsHelpers.member_add_captain_role(member, region)
            # Success
            message = f"You are now the captain of Team: {team_name}"
            return await interaction.followup.send(message)
        except Exception as error:
            message = f"Error: Something went wrong."
            await interaction.followup.send(message)
            raise error

    async def add_player_to_team(
        self, interaction: discord.Interaction, player_name: str
    ):
        """Add a Player to a Team by name"""
        try:
            # This could take a while
            await interaction.response.defer()
            # Get info about the requestor
            requestor = await self.table_player.get_player_record(
                discord_id=interaction.user.id
            )
            if not requestor:
                message = f"You must be registered as a Player to add a Player"
                return await interaction.followup.send(message)
            requestor_player_id = await requestor.get_field(PlayerFields.record_id)
            requestor_team_player = (
                await self.table_team_player.get_team_player_records(
                    player_id=requestor_player_id
                )
            )
            requestor_team_player = requestor_team_player[0]
            if not requestor_team_player:
                message = f"You must be on a Team to add a Player."
                return await interaction.followup.send(message)
            requestor_is_captain = await self.related_records.is_any_captain(requestor)
            if not requestor_is_captain:
                message = f"You must be a Team captain to add a Player."
                return await interaction.followup.send(message)
            # Get info about the Team and new Player
            team_id = await requestor_team_player.get_field(TeamPlayerFields.team_id)
            team: TeamRecord = await self.table_team.get_team_record(record_id=team_id)
            player = await self.table_player.get_player_record(player_name=player_name)
            player_id = await player.get_field(PlayerFields.record_id)
            existing_team = await self.related_records.get_team_from_player(player)
            if existing_team:
                existing_team_name = await existing_team.get_field(TeamFields.team_name)
                message = f"Player is already on a Team: {existing_team_name}"
                return await interaction.followup.send(message)
            # Add the Player to the Team
            await self.table_team_player.create_team_player_record(
                team_id=team_id,
                player_id=player_id,
            )
            # Update Player's Discord roles
            player_discord_id = await player.get_field(PlayerFields.discord_id)
            player_discord_member = await discord_helpers.member_from_discord_id(
                guild=interaction.guild,
                discord_id=player_discord_id,
            )
            team_name = await team.get_field(TeamFields.team_name)
            await ManageTeamsHelpers.member_remove_team_roles(player_discord_member)
            await ManageTeamsHelpers.member_add_team_role(
                player_discord_member, team_name
            )
            # Success
            message = f"Player '{player_name}' added to Team '{team_name}'"
            return await interaction.followup.send(message)
        except Exception as error:
            message = f"Error: Something went wrong."
            await interaction.followup.send(message)
            raise error

    async def remove_player_from_team(
        self, interaction: discord.Interaction, player_name: str
    ):
        """Remove a Player from a Team by name"""
        try:
            # This could take a while
            await interaction.response.defer()
            # Get info about the requestor
            requestor = await self.table_player.get_player_record(
                discord_id=interaction.user.id
            )
            if not requestor:
                message = f"You must be registered as a Player to remove a Player from a Team."
                return await interaction.followup.send(message)
            requestor_player_id = await requestor.get_field(PlayerFields.record_id)
            requestor_team_player = (
                await self.table_team_player.get_team_player_records(
                    player_id=requestor_player_id
                )
            )
            requestor_team_player = requestor_team_player[0]
            if not requestor_team_player:
                message = f"You must be on a Team to remove a Player."
                return await interaction.followup.send(message)
            requestor_is_captain = await self.related_records.is_any_captain(requestor)
            if not requestor_is_captain:
                message = f"You must be a Team captain to remove a Player."
                return await interaction.followup.send(message)
            # Get info about the Team and Player to remove
            team_id = await requestor_team_player.get_field(TeamPlayerFields.team_id)
            player = await self.table_player.get_player_record(player_name=player_name)
            player_id = await player.get_field(PlayerFields.record_id)
            team_player = await self.table_team_player.get_team_player_records(
                team_id=team_id, player_id=player_id
            )
            if not team_player:
                message = f"Player is not on the Team: {player_name}"
                return await interaction.followup.send(message)
            team_player = team_player[0]
            player_is_captain = await team_player.get_field(TeamPlayerFields.is_captain)
            if player_is_captain:
                message = f"Cannot remove main Team captain: {player_name}"
                return await interaction.followup.send(message)
            # Remove the Player from the Team
            await self.table_team_player.delete_team_player_record(
                team_id=team_id,
                player_id=player_id,
            )
            # Update Player's Discord roles
            player_discord_id = await player.get_field(PlayerFields.discord_id)
            player_discord_member = await discord_helpers.member_from_discord_id(
                guild=interaction.guild,
                discord_id=player_discord_id,
            )
            await ManageTeamsHelpers.member_remove_team_roles(player_discord_member)
            # Success
            team: TeamRecord = await self.table_team.get_team_record(team_id=team_id)
            team_name = await team.get_field(TeamFields.team_name)
            message = f"Player '{player_name}' removed from Team '{team_name}'"
            return await interaction.followup.send(message)
        except Exception as error:
            message = f"Error: Something went wrong."
            await interaction.followup.send(message)
            raise error

    async def promote_player_to_captain(
        self, interaction: discord.Interaction, player_name
    ):
        """Promote a Player to Team captain"""
        try:
            # This could take a while
            await interaction.response.defer()
            # Get info about the requestor
            requestor = await self.table_player.get_player_record(
                discord_id=interaction.user.id
            )
            requestor_id = await requestor.get_field(PlayerFields.record_id)
            # Get info about the player
            player = await self.table_player.get_player_record(player_name=player_name)
            player_id = await player.get_field(PlayerFields.record_id)
            # Get info about the team
            team = await self.related_records.get_team_from_player(requestor)
            team_id = await team.get_field(TeamFields.record_id)
            team_players = await self.table_team_player.get_team_player_records(
                team_id=team_id
            )
            captain_id = None
            co_captain_id = None
            player_team_player_record = None
            for team_player in team_players:
                if await team_player.get_field(TeamPlayerFields.is_captain):
                    captain_id = await team_player.get_field(TeamPlayerFields.player_id)
                if await team_player.get_field(TeamPlayerFields.is_co_captain):
                    co_captain_id = await team_player.get_field(
                        TeamPlayerFields.player_id
                    )
                if await team_player.get_field(TeamPlayerFields.player_id) == player_id:
                    player_team_player_record = team_player
            # Get info about the Team captains
            requestor_id = await requestor.get_field(PlayerFields.record_id)
            requestor_is_captain = captain_id == requestor_id
            if not requestor_is_captain:
                message = f"You must be the Team captain to promote a Player."
                return await interaction.followup.send(message)
            if co_captain_id:
                message = f"Team already has a co-captain."
                return await interaction.followup.send(message)
            region = await requestor.get_field(PlayerFields.region)
            # Update Player's TeamPlayer record
            if not player_team_player_record:
                message = f"Player is not on the Team: {player_name}"
                return await interaction.followup.send(message)
            await player_team_player_record.set_field(
                TeamPlayerFields.is_co_captain, True
            )
            await self.table_team_player.update_team_player_record(
                player_team_player_record
            )
            # Update Player's Discord roles
            player_discord_id = await player.get_field(PlayerFields.discord_id)
            player_discord_member = await discord_helpers.member_from_discord_id(
                guild=interaction.guild,
                discord_id=player_discord_id,
            )
            await ManageTeamsHelpers.member_add_captain_role(
                player_discord_member, region
            )
            # Success
            message = f"Player '{player_name}' promoted to co-captain"
            return await interaction.followup.send(message)
        except Exception as error:
            message = f"Error: Something went wrong."
            await interaction.followup.send(message)
            raise error

    async def demote_player_from_captain(
        self, interaction: discord.Interaction, player_name
    ):
        """Demote a Player from Team captain"""
        try:
            # This could take a while
            await interaction.response.defer()
            # Get info about the requestor
            requestor = await self.table_player.get_player_record(
                discord_id=interaction.user.id
            )
            requestor_id = await requestor.get_field(PlayerFields.record_id)
            # Get info about the player
            player = await self.table_player.get_player_record(player_name=player_name)
            player_id = await player.get_field(PlayerFields.record_id)
            # Get info about the team
            team = await self.related_records.get_team_from_player(requestor)
            team_id = await team.get_field(TeamFields.record_id)
            team_name = await team.get_field(TeamFields.team_name)
            team_players = await self.table_team_player.get_team_player_records(
                team_id=team_id
            )
            captain_id = None
            co_captain_id = None
            player_team_player_record = None
            for team_player in team_players:
                if await team_player.get_field(TeamPlayerFields.is_captain):
                    captain_id = await team_player.get_field(TeamPlayerFields.player_id)
                if await team_player.get_field(TeamPlayerFields.is_co_captain):
                    co_captain_id = await team_player.get_field(
                        TeamPlayerFields.player_id
                    )
                if await team_player.get_field(TeamPlayerFields.player_id) == player_id:
                    player_team_player_record = team_player
            # Get info about the Team captains
            requestor_is_captain = captain_id == requestor_id
            player_is_co_captain = co_captain_id == player_id
            if not requestor_is_captain:
                message = f"You must be the Team captain to demote a Player."
                return await interaction.followup.send(message)

            if not player_is_co_captain:
                message = f"Player is not a co-captain."
                return await interaction.followup.send(message)
            # Update Player's TeamPlayer record
            if not player_team_player_record:
                message = f"Player is not on the Team: {player_name}"
                return await interaction.followup.send(message)
            await player_team_player_record.set_field(
                TeamPlayerFields.is_co_captain, False
            )
            await self.table_team_player.update_team_player_record(
                player_team_player_record
            )
            # Update Player's Discord roles
            player_discord_id = await player.get_field(PlayerFields.discord_id)
            player_discord_member = await discord_helpers.member_from_discord_id(
                guild=interaction.guild,
                discord_id=player_discord_id,
            )
            await ManageTeamsHelpers.member_remove_captain_role(player_discord_member)
            # Success
            message = f"Player '{player_name}' demoted from co-captain"
            return await interaction.followup.send(message)
        except Exception as error:
            message = f"Error: Something went wrong."
            await interaction.followup.send(message)
            raise error

    async def leave_team(self, interaction: discord.Interaction):
        """Remove the requestor from their Team"""
        try:
            # This could take a while
            await interaction.response.defer()
            # Get info about the requestor
            requestor = await self.table_player.get_player_record(
                discord_id=interaction.user.id
            )
            if not requestor:
                message = f"You must be registered as a Player to leave a Team."
                return await interaction.followup.send(message)
            requestor_player_id = await requestor.get_field(PlayerFields.record_id)
            requestor_team_player = (
                await self.table_team_player.get_team_player_records(
                    player_id=requestor_player_id
                )
            )
            requestor_team_player = (
                requestor_team_player[0] if requestor_team_player else None
            )
            if not requestor_team_player:
                message = f"You must be on a Team to leave."
                return await interaction.followup.send(message)
            # Get info about the Team
            team_id = await requestor_team_player.get_field(TeamPlayerFields.team_id)
            team: TeamRecord = await self.table_team.get_team_record(record_id=team_id)
            team_name = await team.get_field(TeamFields.team_name)
            # Get info about the captains
            team_players = await self.table_team_player.get_team_player_records(
                team_id=team_id
            )
            captain_team_player = None
            co_captain_team_player = None
            requestor_team_player = None
            for team_player in team_players:
                player_id = await team_player.get_field(TeamPlayerFields.player_id)
                if player_id == requestor_player_id:
                    requestor_team_player = team_player
                if await team_player.get_field(TeamPlayerFields.is_captain):
                    captain_team_player = team_player
                if await team_player.get_field(TeamPlayerFields.is_co_captain):
                    co_captain_team_player = team_player
            captain_id = await captain_team_player.get_field(TeamPlayerFields.player_id)
            co_captain_id = (
                await co_captain_team_player.get_field(TeamPlayerFields.player_id)
                if co_captain_team_player
                else None
            )
            if captain_id == requestor_player_id:
                if not co_captain_id:
                    message = f"Cannot leave as main Team captain without a co-captain."
                    return await interaction.followup.send(message)
                # promote the co-captain to captain
                await co_captain_team_player.set_field(
                    TeamPlayerFields.is_captain, True
                )
                await co_captain_team_player.set_field(
                    TeamPlayerFields.is_co_captain, False
                )
            # Remove the Player from the Team
            await self.table_team_player.delete_team_player_record(
                requestor_team_player
            )
            # Update Player's Discord roles
            member = interaction.user
            await ManageTeamsHelpers.member_remove_team_roles(member)
            # Success
            message = f"You have left Team '{team_name}'"
            return await interaction.followup.send(message)
        except Exception as error:
            message = f"Error: Something went wrong."
            await interaction.followup.send(message)
            raise error

    async def disband_team(self, interaction: discord.Interaction):
        """Disband the requestor's Team"""
        try:
            # This could take a while
            await interaction.response.defer()
            # Get info about the requestor
            requestor = await self.table_player.get_player_record(
                discord_id=interaction.user.id
            )
            if not requestor:
                message = f"You must be registered as a Player to disband a Team."
                return await interaction.followup.send(message)
            requestor_player_id = await requestor.get_field(PlayerFields.record_id)
            requestor_team_players = (
                await self.table_team_player.get_team_player_records(
                    player_id=requestor_player_id
                )
            )
            requestor_team_player = (
                requestor_team_players[0] if requestor_team_players else None
            )
            if not requestor_team_player:
                message = f"You must be on a Team to disband."
                return await interaction.followup.send(message)
            requestor_is_captain = await requestor_team_player.get_field(
                TeamPlayerFields.is_captain
            )
            if not requestor_is_captain:
                message = f"You must be the main Team captain to disband a Team."
                return await interaction.followup.send(message)
            # Get info about the Team
            team_id = await requestor_team_player.get_field(TeamPlayerFields.team_id)
            team: TeamRecord = await self.table_team.get_team_record(record_id=team_id)
            team_name = await team.get_field(TeamFields.team_name)
            # Remove all Players from the Team
            team_players = await self.table_team_player.get_team_player_records(
                team_id=team_id
            )
            for team_player in team_players:
                player_id = await team_player.get_field(TeamPlayerFields.player_id)
                player = await self.table_player.get_player_record(record_id=player_id)
                player_discord_id = await player.get_field(PlayerFields.discord_id)
                player_discord_member = await discord_helpers.member_from_discord_id(
                    guild=interaction.guild,
                    discord_id=player_discord_id,
                )
                await ManageTeamsHelpers.member_remove_team_roles(player_discord_member)
                await self.table_team_player.delete_team_player_record(team_player)
            # Delete the Team
            await self.table_team.delete_team_record(team)
            # Success
            message = f"Team '{team_name}' has been disbanded"
            return await interaction.followup.send(message)
        except Exception as error:
            message = f"Error: Something went wrong."
            await interaction.followup.send(message)
            raise error

    async def get_team_details(self, interaction: discord.Interaction, team_name: str):
        """Get a Team by name"""
        try:
            # This could take a while
            await interaction.response.defer()
            # Get the Team
            team = await self.table_team.get_team_record(team_name=team_name)
            if not team:
                message = f"Team not found: {team_name}"
                return await interaction.followup.send(message)
            # Get team players
            players = await self.related_records.get_player_records_from_team(team)
            # Format the message
            message_dict = {
                "team": await team.to_dict(),
                "players": [await player.to_dict() for player in players],
            }
            message = await bot_helpers.format_json(message_dict)
            return await interaction.followup.send(message)
        except Exception as error:
            message = f"Error: Something went wrong."
            await interaction.followup.send(message)
            raise error


class ManageTeamsHelpers:
    """EML Team Management Helpers"""

    ### DISCORD ###

    @staticmethod
    async def member_remove_team_roles(member: discord.Member):
        """Remove all Team roles from a Guild Member"""
        prefixes = [constants.ROLE_PREFIX_TEAM, constants.ROLE_PREFIX_CAPTAIN]
        for role in member.roles:
            if any(role.name.startswith(prefix) for prefix in prefixes):
                await member.remove_roles(role)
        return True

    @staticmethod
    async def member_add_team_role(member: discord.Member, team_name: str):
        """Add a Team role to a Guild Member"""
        role_name = f"{constants.ROLE_PREFIX_TEAM}{team_name}"
        role = await discord_helpers.guild_role_get_or_create(member.guild, role_name)
        await member.add_roles(role)
        return True

    @staticmethod
    async def member_add_captain_role(member: discord.Member, region: str):
        """Add a Captain role to a Guild Member"""
        role_name = f"{constants.ROLE_PREFIX_CAPTAIN}{region}"
        role = await discord_helpers.guild_role_get_or_create(member.guild, role_name)
        await member.add_roles(role)
        return True

    @staticmethod
    async def member_remove_captain_role(member: discord.Member):
        """Remove a Captain role from a Guild Member"""
        prefixes = [constants.ROLE_PREFIX_CAPTAIN]
        for role in member.roles:
            if any(role.name.startswith(prefix) for prefix in prefixes):
                await member.remove_roles(role)
        return True
