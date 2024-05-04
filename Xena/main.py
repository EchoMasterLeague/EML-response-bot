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


@bot.tree.command(name=f"{BOT_PREFIX}player_lookup")
async def bot_player_lookup(
    interaction: discord.Interaction, player_name: str = None, discord_id: str = None
):
    """Lookup a Player by name or Discord ID"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_players.get_player_details(interaction, player_name, discord_id)


@bot.tree.command(name=f"{BOT_PREFIX}register_as_player")
async def bot_player_register(interaction: discord.Interaction, region: str = None):
    """Register to become a Player"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_players.register_player(interaction=interaction, region=region)


@bot.tree.command(name=f"{BOT_PREFIX}unregister_as_player")
async def bot_player_unregister(interaction: discord.Interaction):
    """Unregister as a Player"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_players.unregister_player(interaction)


#####################
### Team Commands ###
#####################


@bot.tree.command(name=f"{BOT_PREFIX}team_lookup")
async def bot_team_lookup(interaction: discord.Interaction, team_name: str = None):
    """Lookup a Team by name"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_teams.get_team_details(interaction, team_name)


@bot.tree.command(name=f"{BOT_PREFIX}create_team")
async def bot_team_register(interaction: discord.Interaction, team_name: str):
    """Create a new Team"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_teams.register_team(interaction, team_name)


# @bot.tree.command(name=f"{BOT_PREFIX}add_player")
# async def bot_team_add_player(interaction: discord.Interaction, player_name: str):
#    """Add a new player to your Team"""
#    if await manage_commands.is_command_allowed(interaction):
#        await manage_teams.add_player_to_team(interaction, player_name)


@bot.tree.command(name=f"{BOT_PREFIX}invite_player")
async def bot_team_invite_player(interaction: discord.Interaction, player_name: str):
    """Invite a player to join your Team"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_teams.invite_player_to_team(interaction, player_name)


@bot.tree.command(name=f"{BOT_PREFIX}accept_invite")
async def bot_team_accept_invite(interaction: discord.Interaction):
    """Accept an invite to join a Team"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_teams.accept_invite(interaction)
    # TODO: make team active with at least 4 players


@bot.tree.command(name=f"{BOT_PREFIX}remove_player")
async def bot_team_remove_player(interaction: discord.Interaction, player_name: str):
    """Remove a player from your Team"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_teams.remove_player_from_team(interaction, player_name)
    # TODO: make team inactive under 4 players


@bot.tree.command(name=f"{BOT_PREFIX}promote_player")
async def bot_team_promote_player(interaction: discord.Interaction, player_name: str):
    """Promote a player to Team Captain"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_teams.promote_player_to_co_captain(interaction, player_name)


@bot.tree.command(name=f"{BOT_PREFIX}demote_player")
async def bot_team_demote_player(interaction: discord.Interaction, player_name: str):
    """Demote a player from Team Captain"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_teams.demote_player_from_co_captain(interaction, player_name)


@bot.tree.command(name=f"{BOT_PREFIX}leave_team")
async def bot_team_leave(interaction: discord.Interaction):
    """Leave your current Team"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_teams.leave_team(interaction)
    # TODO: make team inactive under 4 players


@bot.tree.command(name=f"{BOT_PREFIX}disband_team")
async def bot_team_disband(interaction: discord.Interaction):
    """Disband your Team"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_teams.disband_team(interaction)


######################
### Match Commands ###
######################


@bot.tree.command(name=f"{BOT_PREFIX}propose_match")
async def bot_match_propose(
    interaction: discord.Interaction, team_name: str, opponent_name: str, date: str
):
    """Propose a Match with another Team"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_matches.send_match_invite(interaction, opponent_name, date)


@bot.tree.command(name=f"{BOT_PREFIX}accept_match")
async def bot_match_accept(interaction: discord.Interaction):
    """Accept a Match with another Team"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_matches.accept_match_invite(interaction)


@bot.tree.command(name=f"{BOT_PREFIX}propose_result")
async def bot_match_propose_result(
    interaction: discord.Interaction,
    opponent_name: str,
    round_one_scores: str,
    round_two_scores: str,
    round_three_scores: str = None,
):
    """Propose a Match Result with another Team"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_matches.send_result_invite(
            interaction,
            opponent_name,
            round_one_scores,
            round_two_scores,
            round_three_scores,
        )


@bot.tree.command(name=f"{BOT_PREFIX}accept_result")
async def bot_match_accept_result(interaction: discord.Interaction):
    """Accept a Match Result with another Team"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_matches.accept_result_invite(interaction)


###^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^###
###                                          Bot Commands End                                                       ###
#######################################################################################################################


### Run Bot ###
bot.run(DISCORD_TOKEN)
