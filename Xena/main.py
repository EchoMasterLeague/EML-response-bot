from bot_functions.manage_commands import ManageCommands
from bot_functions.manage_players import ManagePlayers
from bot_functions.manage_teams import ManageTeams
from bot_functions.manage_matches import ManageMatches
from database.database_core import CoreDatabase
from database.database_full import FullDatabase
import discord
import discord.ext.commands as commands
import dotenv
import gspread
import os


# Configuration
dotenv.load_dotenv(".secrets/.env")
GOOGLE_CREDENTIALS_FILE = ".secrets/google_credentials.json"
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GUILD_ID = os.environ.get("GUILD_ID")
BOT_PREFIX = os.environ.get("BOT_PREFIX")
BOT_PREFIX = BOT_PREFIX if BOT_PREFIX else "eml"
BOT_PREFIX = BOT_PREFIX + "_" if BOT_PREFIX[-1] != "_" else BOT_PREFIX


# Google Sheets "Database"
gs_client = gspread.service_account(GOOGLE_CREDENTIALS_FILE)
database_core = CoreDatabase(gs_client)
database = FullDatabase(database_core)

# Bot Functions
manage_players = ManagePlayers(database)
manage_teams = ManageTeams(database)
manage_commands = ManageCommands(database)
manage_matches = ManageMatches(database)

# Discord Intents
intents = discord.Intents.default()
intents.messages = True
intents.members = True
intents.message_content = True

# Discord Bot
# bot = commands.Bot(command_prefix=".", intents=intents)
bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())


@bot.event
async def on_ready():
    """Event triggered when the bot is ready."""
    if GUILD_ID:
        guild = await bot.fetch_guild(int(GUILD_ID))
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
    else:
        synced = await bot.tree.sync()
    print(f"synced {len(synced)} command(s)")
    command_list = []
    for thing in synced:
        command_list.append(thing.name)
    command_list.sort()
    for thing in command_list:
        print(thing)


#######################################################################################################################
###                                          Bot Commands Begin                                                     ###
###vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv###

#######################
### Player Commands ###
#######################


@bot.tree.command(name=f"{BOT_PREFIX}lookup_player")
async def bot_lookup_player(
    interaction: discord.Interaction, player_name: str = None, discord_id: str = None
):
    """Lookup a Player by name or Discord ID"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_players.get_player_details(interaction, player_name, discord_id)


@bot.tree.command(name=f"{BOT_PREFIX}player_register")
async def bot_player_register(interaction: discord.Interaction, region: str = None):
    """Register to become a Player"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_players.register_player(interaction=interaction, region=region)


@bot.tree.command(name=f"{BOT_PREFIX}player_unregister")
async def bot_player_unregister(interaction: discord.Interaction):
    """Unregister as a Player"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_players.unregister_player(interaction)


#####################
### Team Commands ###
#####################


@bot.tree.command(name=f"{BOT_PREFIX}lookup_team")
async def bot_lookup_team(interaction: discord.Interaction, team_name: str = None):
    """Lookup a Team by name"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_teams.get_team_details(interaction, team_name)


@bot.tree.command(name=f"{BOT_PREFIX}team_create")
async def bot_team_create(interaction: discord.Interaction, team_name: str):
    """Create a new Team"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_teams.create_team(interaction, team_name)


@bot.tree.command(name=f"{BOT_PREFIX}team_invite_offer")
async def bot_team_invite_offer(interaction: discord.Interaction, player_name: str):
    """Invite a player to join your Team"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_teams.invite_player_to_team(interaction, player_name)


@bot.tree.command(name=f"{BOT_PREFIX}team_invite_accept")
async def bot_team_invite_accept(interaction: discord.Interaction):
    """Accept an invite to join a Team"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_teams.accept_invite(interaction)
    # TODO: make team active with at least 4 players


@bot.tree.command(name=f"{BOT_PREFIX}team_player_remove")
async def bot_team_player_remove(interaction: discord.Interaction, player_name: str):
    """Remove a player from your Team"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_teams.remove_player_from_team(interaction, player_name)
    # TODO: make team inactive under 4 players


@bot.tree.command(name=f"{BOT_PREFIX}team_player_promote")
async def bot_team_player_promote(interaction: discord.Interaction, player_name: str):
    """Promote a player to Team Co-Captain"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_teams.promote_player_to_co_captain(interaction, player_name)


@bot.tree.command(name=f"{BOT_PREFIX}team_player_demote")
async def bot_team_player_demote(interaction: discord.Interaction, player_name: str):
    """Demote a player from Team Co-Captain"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_teams.demote_player_from_co_captain(interaction, player_name)


@bot.tree.command(name=f"{BOT_PREFIX}team_leave")
async def bot_team_leave(interaction: discord.Interaction):
    """Leave your current Team"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_teams.leave_team(interaction)
    # TODO: make team inactive under 4 players


@bot.tree.command(name=f"{BOT_PREFIX}team_disband")
async def bot_team_disband(interaction: discord.Interaction):
    """Disband your Team"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_teams.disband_team(interaction)


######################
### Match Commands ###
######################


@bot.tree.command(name=f"{BOT_PREFIX}match_offer")
async def bot_match_propose(
    interaction: discord.Interaction, opponent_name: str, date: str
):
    """Propose a Match with another Team"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_matches.send_match_invite(interaction, opponent_name, date)


@bot.tree.command(name=f"{BOT_PREFIX}match_accept")
async def bot_match_accept(
    interaction: discord.Interaction, match_invite_id: str = None
):
    """Accept a Match with another Team"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_matches.accept_match_invite(interaction, match_invite_id)


@bot.tree.command(name=f"{BOT_PREFIX}match_result_offer")
async def bot_match_result_offer(
    interaction: discord.Interaction,
    opponent_name: str,
    outcome: str,
    scores: str,
):
    """Propose a Match Result with another Team"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_matches.send_result_invite(
            interaction, opponent_name, scores, outcome
        )


@bot.tree.command(name=f"{BOT_PREFIX}match_result_accept")
async def bot_match_result_accept(interaction: discord.Interaction):
    """Accept a Match Result with another Team"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_matches.accept_result_invite(interaction)


###^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^###
###                                          Bot Commands End                                                       ###
#######################################################################################################################


### Run Bot ###
bot.run(DISCORD_TOKEN)
