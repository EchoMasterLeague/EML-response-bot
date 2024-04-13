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
bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())
# bot = commands.Bot(command_prefix=".", intents=intents)


@bot.event
async def on_ready():
    """Event triggered when the bot is ready."""
    try:
        synced = await bot.tree.sync()
        print(f"synced {len(synced)} command(s)")
    except Exception as e:
        print("Error:", e)


#######################################################################################################################
###                                          Bot Commands Begin                                                     ###
###vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv###

#######################
### Player Commands ###
#######################


@bot.tree.command(name="eml_register_as_player")
async def bot_player_register(interaction: discord.Interaction, region: str = "NA"):
    """Register to become a Player"""
    await interaction.response.send_message(
        await manage_players.register_player(
            discord_id=interaction.user.id,
            player_name=interaction.user.display_name,
            region=region,
        )
    )


@bot.tree.command(name="eml_player_lookup")
async def bot_player_lookup(
    interaction: discord.Interaction, player_name: str = None, discord_id: str = None
):
    """Lookup a Player by name or Discord ID"""
    await interaction.response.send_message(
        await manage_players.get_player_details(
            player_name=player_name, discord_id=discord_id
        )
    )


#####################
### Team Commands ###
#####################


@bot.tree.command(name="eml_create_team")
async def bot_team_register(interaction: discord.Interaction, team_name: str):
    """Create a new Team"""
    await interaction.response.send_message(
        await manage_teams.register_team(
            interaction=interaction,
            team_name=team_name,
            discord_id=interaction.user.id,
        )
    )


@bot.tree.command(name="eml_add_player")
async def bot_team_register(interaction: discord.Interaction, team_name: str):
    """Add a new player to your Team"""
    await interaction.response.send_message(await manage_teams.register_team(team_name))


@bot.tree.command(name="eml_team_lookup")
async def bot_team_lookup(interaction: discord.Interaction, team_name: str):
    """Lookup a Team by name"""
    await interaction.response.send_message(
        await manage_teams.get_team_details(team_name)
    )


###^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^###
###                                          Bot Commands End                                                       ###
#######################################################################################################################


### Run Bot ###
bot.run(DISCORD_TOKEN)
