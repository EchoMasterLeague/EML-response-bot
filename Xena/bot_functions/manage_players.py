from bot_dialogues import choices
from database.database_full import FullDatabase
from database.enums import Regions
from database.fields import CooldownFields, PlayerFields, TeamFields, TeamPlayerFields
from database.records import CooldownRecord
from errors import database_errors
from utils import discord_helpers, general_helpers
import constants
import datetime
import discord


class ManagePlayers:
    """EML Player Management"""

    def __init__(self, database: FullDatabase):
        self._db = database

    async def register_player(
        self,
        interaction: discord.Interaction,
        region: str = None,
        log_channel: discord.TextChannel = None,
    ):
        """Create a new Player"""
        try:
            # Get region
            if region:
                # This could take a while
                await interaction.response.defer()
            else:
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
            region = await ManagePlayersHelpers.normalize_region(region)
            assert region, f"Region must be in {allowed_regions}"
            # Check for existing Players with the same DisplayName or Discord ID
            existing_players = await self._db.table_player.get_player_records(
                discord_id=discord_id
            )
            assert not existing_players, "You are already registered."
            existing_players = await self._db.table_player.get_player_records(
                player_name=player_name
            )
            assert not existing_players, f"Player name {player_name} already in use."
            # Create Player record
            await self._db.table_player.create_player_record(
                discord_id=discord_id, player_name=player_name, region=region
            )
            # Add Player role
            await ManagePlayersHelpers.member_add_player_role(
                interaction.user, region=region
            )
            # Success
            message = f"Player '{player_name}' registered for region '{region}'"
            await discord_helpers.final_message(interaction, message)
            await discord_helpers.log_to_channel(
                channel=log_channel,
                message=f"{interaction.user.mention} has joined the League.",
            )
        except AssertionError as message:
            await discord_helpers.final_message(interaction, message)
        except Exception as error:
            await discord_helpers.error_message(interaction, error)

    async def unregister_player(
        self, interaction: discord.Interaction, log_channel: discord.TextChannel = None
    ):
        """Unregister a Player"""
        try:
            # This could take a while
            await interaction.response.defer()
            # Get Player info
            discord_id = interaction.user.id
            existing_players = await self._db.table_player.get_player_records(
                discord_id=discord_id
            )

            assert existing_players, "You are not registered."
            existing_player = existing_players[0]
            existing_player_id = await existing_player.get_field(PlayerFields.record_id)
            existing_team_players = (
                await self._db.table_team_player.get_team_player_records(
                    player_id=existing_player_id
                )
            )
            assert not existing_team_players, "You must leave your team first."
            # Remove Player role
            await ManagePlayersHelpers.member_remove_player_role(interaction.user)
            # Delete Player record
            await self._db.table_player.delete_player_record(existing_player)
            # Success
            message = f"You are no longer registered as a player"
            await discord_helpers.final_message(interaction, message)
            await discord_helpers.log_to_channel(
                channel=log_channel,
                message=f"{interaction.user.mention} has left the League.",
            )
        except AssertionError as message:
            await discord_helpers.final_message(interaction, message)
        except Exception as error:
            await discord_helpers.error_message(interaction, error)

    async def get_player_details(
        self,
        interaction: discord.Interaction,
        player_name: str = None,
        discord_id: str = None,
    ):
        """Get a Player by name or Discord ID"""
        try:
            # This could take a while
            await interaction.response.defer()
            # Get Player info
            if not discord_id and not player_name:
                discord_id = interaction.user.id
            players = await self._db.table_player.get_player_records(
                discord_id=discord_id, player_name=player_name
            )
            assert players, "Player not found."
            player = players[0]
            player_name = await player.get_field(PlayerFields.player_name)
            player_region = await player.get_field(PlayerFields.region)
            player_id = await player.get_field(PlayerFields.record_id)
            message_dict = {}
            message_dict["player"] = player_name
            message_dict["region"] = player_region
            # Get cooldown info
            cooldowns = await self._db.table_cooldown.get_cooldown_records(
                player_id=player_id
            )
            cooldown: CooldownRecord = cooldowns[0] if cooldowns else None
            if cooldown:
                cooldown_end = await cooldown.get_field(CooldownFields.expires_at)
                message_dict["cooldown_end"] = cooldown_end
            # Get Team info
            team_players = await self._db.table_team_player.get_team_player_records(
                player_id=player_id
            )
            team_player = team_players[0] if team_players else None
            if team_player:
                team_id = await team_player.get_field(TeamPlayerFields.team_id)
                teams = await self._db.table_team.get_team_records(record_id=team_id)
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
            # Create Response
            message = await general_helpers.format_json(message_dict)
            message = await discord_helpers.code_block(message, language="json")
            return await discord_helpers.final_message(interaction, message)
        except AssertionError as message:
            await discord_helpers.final_message(interaction, message)
        except Exception as error:
            await discord_helpers.error_message(interaction, error)

    async def get_cooldown_players(self, interaction: discord.Interaction):
        """Get all Players on cooldown"""
        try:
            # This could take a while
            await interaction.response.defer()
            # Get Cooldown info
            cooldowns = await self._db.table_cooldown.get_cooldown_records(
                expires_after=datetime.datetime.now().timestamp()
            )
            assert cooldowns, "No players on cooldown."
            cooldown_players = {}
            for cooldown in cooldowns:
                player_name = await cooldown.get_field(CooldownFields.vw_player)
                former_team = await cooldown.get_field(CooldownFields.vw_old_team)
                created_at = await cooldown.get_field(CooldownFields.created_at)
                cooldown_players[player_name] = f"{former_team} ({created_at})"
            # Create Response
            message = await general_helpers.format_json(cooldown_players)
            message = await discord_helpers.code_block(message, language="json")
            message = f"Players on cooldown:\n{message}"
            return await discord_helpers.final_message(interaction, message)
        except AssertionError as message:
            await discord_helpers.final_message(interaction, message)
        except Exception as error:
            await discord_helpers.error_message(interaction, error)


class ManagePlayersHelpers:
    """EML Player Management Helpers"""

    @staticmethod
    async def member_add_player_role(member: discord.Member, region: str):
        """Add a Captain role to a Guild Member"""
        role_name = f"{constants.ROLE_PREFIX_PLAYER}{region}"
        role = await discord_helpers.guild_role_get_or_create(member.guild, role_name)
        await member.add_roles(role)
        return True

    @staticmethod
    async def member_remove_player_role(member: discord.Member):
        """Remove a Captain role from a Guild Member"""
        prefixes = [constants.ROLE_PREFIX_PLAYER]
        for role in member.roles:
            if any(role.name.startswith(prefix) for prefix in prefixes):
                await member.remove_roles(role)
        return True

    @staticmethod
    async def normalize_region(region: str):
        """Normalize a region string"""
        allowed_regions = [r.value for r in Regions]
        for allowed_region in allowed_regions:
            if str(region).casefold() == str(allowed_region).casefold():
                return allowed_region
        return None
