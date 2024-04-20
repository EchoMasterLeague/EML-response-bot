from bot_functions.manage_players import ManagePlayers
from bot_functions.manage_teams import ManageTeams
from database.database import Database
import discord
import discord.ext.commands as commands
import dotenv
import gspread
import os


# Configuration
dotenv.load_dotenv(".secrets/.env")
GOOGLE_CREDENTIALS_FILE = ".secrets/google_credentials.json"
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
BOT_PREFIX = os.environ.get("BOT_PREFIX")
BOT_PREFIX = BOT_PREFIX if BOT_PREFIX else "eml"
GUILD_ID = os.environ.get("GUILD_ID")

# Google Sheets "Database"
gs_client = gspread.service_account(GOOGLE_CREDENTIALS_FILE)
database = Database(gs_client)
manage_players = ManagePlayers(database)
manage_teams = ManageTeams(database)

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


@bot.tree.command(name=f"{BOT_PREFIX}_player_lookup")
async def bot_player_lookup(
    interaction: discord.Interaction, player_name: str = None, discord_id: str = None
):
    """Lookup a Player by name or Discord ID"""
    await manage_players.get_player_details(interaction, player_name, discord_id)


@bot.tree.command(name=f"{BOT_PREFIX}_register_as_player")
async def bot_player_register(interaction: discord.Interaction, region: str = None):
    """Register to become a Player"""
    await manage_players.register_player(interaction=interaction, region=region)


@bot.tree.command(name=f"{BOT_PREFIX}_unregister_as_player")
async def bot_player_unregister(interaction: discord.Interaction):
    """Unregister as a Player"""
    await manage_players.unregister_player(interaction)


#####################
### Team Commands ###
#####################


@bot.tree.command(name=f"{BOT_PREFIX}_team_lookup")
async def bot_team_lookup(interaction: discord.Interaction, team_name: str):
    """Lookup a Team by name"""
    await manage_teams.get_team_details(interaction, team_name)


@bot.tree.command(name=f"{BOT_PREFIX}_create_team")
async def bot_team_register(interaction: discord.Interaction, team_name: str):
    """Create a new Team"""
    await manage_teams.register_team(interaction, team_name)


@bot.tree.command(name=f"{BOT_PREFIX}_add_player")
async def bot_team_add_player(interaction: discord.Interaction, player_name: str):
    """Add a new player to your Team"""
    await manage_teams.add_player_to_team(interaction, player_name)


@bot.tree.command(name=f"{BOT_PREFIX}_remove_player")
async def bot_team_remove_player(interaction: discord.Interaction, player_name: str):
    """Remove a player from your Team"""
    await manage_teams.remove_player_from_team(interaction, player_name)


@bot.tree.command(name=f"{BOT_PREFIX}_promote_player")
async def bot_team_promote_player(interaction: discord.Interaction, player_name: str):
    """Promote a player to Team Captain"""
    await manage_teams.promote_player_to_co_captain(interaction, player_name)


@bot.tree.command(name=f"{BOT_PREFIX}_demote_player")
async def bot_team_demote_player(interaction: discord.Interaction, player_name: str):
    """Demote a player from Team Captain"""
    await manage_teams.demote_player_from_co_captain(interaction, player_name)


@bot.tree.command(name=f"{BOT_PREFIX}_leave_team")
async def bot_team_leave(interaction: discord.Interaction):
    """Leave your current Team"""
    await manage_teams.leave_team(interaction)


@bot.tree.command(name=f"{BOT_PREFIX}_disband_team")
async def bot_team_disband(interaction: discord.Interaction):
    """Disband your Team"""
    await manage_teams.disband_team(interaction)


###^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^###
###                                          Bot Commands End                                                       ###
#######################################################################################################################


### Run Bot ###
bot.run(DISCORD_TOKEN)
