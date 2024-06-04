from database.database_core import CoreDatabase
from database.database_full import FullDatabase
import bot_functions
import discord
import discord.ext.commands as commands
import dotenv
import gspread
import os
import utils.discord_helpers as discord_helpers

# Configuration
THIS_DIR = os.path.dirname(__file__)
SECRETS_DIR = os.environ.get("SECRETS_DIR")
SECRETS_DIR = SECRETS_DIR if SECRETS_DIR else os.path.join(THIS_DIR, ".secrets")
dotenv.load_dotenv()
dotenv.load_dotenv(os.path.join(SECRETS_DIR, ".env"))
GOOGLE_CREDENTIALS_FILE = os.path.join(SECRETS_DIR, "google_credentials.json")

# Environment Variables
BOT_PREFIX = os.environ.get("BOT_PREFIX")
BOT_PREFIX = BOT_PREFIX.rstrip("_") + "_" if BOT_PREFIX else ""
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GUILD_ID = os.environ.get("GUILD_ID")

# Google Sheets "Database"
# gs_client = gspread.service_account(GOOGLE_CREDENTIALS_FILE, http_client=gspread.BackOffHTTPClient)  # For 429 backoff, but breaks on 403
gs_client = gspread.service_account(GOOGLE_CREDENTIALS_FILE)
database_core = CoreDatabase(gs_client)
db = FullDatabase(database_core)

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
    # Sync Commands
    if GUILD_ID:
        guild = await bot.fetch_guild(int(GUILD_ID))
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
    else:
        synced = await bot.tree.sync()

    # Print Synced Commands
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

##############################
### Informational Commands ###
##############################


@bot.tree.command(name=f"{BOT_PREFIX}help")
async def help(interaction: discord.Interaction):
    """
    Displays information about available commands.
    """
    help_message = (
        "Here are the available commands:\n"
        "`/ranks`: Display team rankings.\n"
        "`/matches`: Display season matches and results.\n"
        "`/rosters`: Display team rosters.\n"
        "`/registration`: Display registration information.\n"
        "`/website`: Display the league website.\n"
        "`/instructions`: Instructions for the Commands.\n"
        "`/commands`: The Commands.\n"
        "`/league_rules`: Display league rules.\n"
        "`/server_coc`: Display server Code of Conduct.\n"
        "`/ticket`: Display ticket information.\n"
        "`/support`: Display support information.\n"
        "`/staff_app`: Display staff application link.\n"
        "`/calendar_na`: Display the na league calendar.\n"
        "`/calendar_eu`: Display the eu league calendar.\n"
        "`/eml_action_list`: Display the EML action list.\n"
        "`/list_members <role>`: List members with a specific role."
    )

    await interaction.response.send_message(help_message)


@bot.tree.command(name=f"{BOT_PREFIX}ranks")
async def ranks(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://echomasterleague.com/team-rankings-2/"
    )


@bot.tree.command(name=f"{BOT_PREFIX}matches")
async def matches(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://echomasterleague.com/current-week-matches-and-results/"
    )


@bot.tree.command(name=f"{BOT_PREFIX}rosters")
async def rosters(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://docs.google.com/spreadsheets/d/13vcfXkCejl9I4dtlA9ZI19dHGYh7aWIQXUU5MWhpYt0/edit?usp=sharing"
    )


@bot.tree.command(name=f"{BOT_PREFIX}website")
async def website(interaction: discord.Interaction):
    await interaction.response.send_message(f"https://echomasterleague.com/")


@bot.tree.command(name=f"{BOT_PREFIX}instructions")
async def website(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://docs.google.com/document/d/10GqUfLFMmW2eDP-hCxjJK9uOa-fjONoOpi_88mRJpZY/edit?usp=sharing"
    )


@bot.tree.command(name=f"{BOT_PREFIX}commands")
async def website(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://docs.google.com/document/d/1KeGjbB9urEjVZ_ZM0q6nOwfOgaq2REezFIDGW0EWNXI/edit?usp=sharing"
    )


@bot.tree.command(name=f"{BOT_PREFIX}league_rules")
async def leaguerules(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://echomasterleague.com/eml-league-rules/"
    )


@bot.tree.command(name=f"{BOT_PREFIX}coc")
async def coc(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://discord.com/channels/1182380144887865406/1182380146506866823"
    )


@bot.tree.command(name=f"{BOT_PREFIX}ticket")
async def ticket(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://discord.com/channels/1182380144887865406/1182380148436242475"
    )


@bot.tree.command(name=f"{BOT_PREFIX}support")
async def support(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://discord.com/channels/1182380144887865406/1182380148436242476"
    )


@bot.tree.command(name=f"{BOT_PREFIX}staff_app")
async def staff_app(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://echomasterleague.com/staff-application/"
    )


@bot.tree.command(name=f"{BOT_PREFIX}calendar_na")
async def staff_app(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://cdn.discordapp.com/attachments/1182380149468045354/1239966506297589842/Echo_Master_League_Calendar_.png?ex=6644d84c&is=664386cc&hm=729e9856f260f98d129e1772df43c722779bc4b800045af1ed206c23bdd08f15&"
    )


@bot.tree.command(name=f"{BOT_PREFIX}calendar_eu")
async def staff_app(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://cdn.discordapp.com/attachments/1184569245800083637/1229790087814840340/EML_CAL_EU_1PNG.png?ex=6630f645&is=661e8145&hm=29f34543a8d2f4aa3ddd22025922cbc917523c364f91a808b8581bcad1d003a6&"
    )


@bot.tree.command(name=f"{BOT_PREFIX}ap")
async def ap(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://docs.google.com/spreadsheets/d/e/2PACX-1vSJmIGHxYlgMAy2Wvlz-pSx27iDTjBdzQbe7BCSu6qXCHk1kBTxwDJu0yAQuy0Msm3KLnIY2MwvMC8t/pubhtml"
    )


@bot.tree.command(name=f"{BOT_PREFIX}action_list")
async def action_list(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://docs.google.com/spreadsheets/d/e/2PACX-1vRhkQIBw9ETybdGNVggWnAf9ueizzDMc0lbKcsDPQsD6c1jDd8p8u8OUwl5gdcR2M14KmCV6-eF03p4/pubhtml"
    )


@bot.tree.command(name=f"{BOT_PREFIX}lounge_report")
async def lounge_report(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Gameplay violations such as halfcycling, cheat engine, etc. need to reported with evidence in a ticket to the Echo VR Lounge. Any action taken by EVRL will be considered for action by the EML AP system. https://discord.gg/echo-combat-lounge-779349159852769310"
    )


@bot.tree.command(name=f"{BOT_PREFIX}rolelookup")
async def bot_rolelookup(
    interaction: discord.Interaction,
    role_input1: str,
    role_input2: str = None,
):
    bot_functions.show_role_members(
        interaction=interaction, role_input1=role_input1, role_input2=role_input2
    )


#######################
### System Commands ###
#######################


@bot.tree.command(name=f"{BOT_PREFIX}zdebugdbqueue")
async def bot_z_debug_db_queue(interaction: discord.Interaction):
    """Debug the pending writes"""
    if await bot_functions.command_is_enabled(database=db, interaction=interaction):
        await bot_functions.system_list_writes(database=db, interaction=interaction)


@bot.tree.command(name=f"{BOT_PREFIX}zdebugdbcache")
async def bot_z_debug_db_cache(interaction: discord.Interaction):
    """Debug the local cache"""
    if await bot_functions.command_is_enabled(database=db, interaction=interaction):
        await bot_functions.system_list_cache(database=db, interaction=interaction)


#######################
### Player Commands ###
#######################


@bot.tree.command(name=f"{BOT_PREFIX}lookupplayer")
async def bot_lookup_player(
    interaction: discord.Interaction, player_name: str = None, discord_id: str = None
):
    """Lookup a Player by name or Discord ID"""
    if await bot_functions.command_is_enabled(database=db, interaction=interaction):
        await bot_functions.show_player_details(
            database=db,
            interaction=interaction,
            player_name=player_name,
            discord_id=discord_id,
        )


@bot.tree.command(name=f"{BOT_PREFIX}playerregister")
async def bot_player_register(interaction: discord.Interaction):
    """Register to become a Player"""
    if await bot_functions.command_is_enabled(database=db, interaction=interaction):
        log_channel = await discord_helpers.get_log_channel(guild=interaction.guild)
        await bot_functions.player_register(
            database=db, interaction=interaction, log_channel=log_channel
        )


@bot.tree.command(name=f"{BOT_PREFIX}playerunregister")
async def bot_player_unregister(interaction: discord.Interaction):
    """Unregister as a Player"""
    if await bot_functions.command_is_enabled(database=db, interaction=interaction):
        log_channel = await discord_helpers.get_log_channel(guild=interaction.guild)
        await bot_functions.player_unregister(
            database=db, interaction=interaction, log_channel=log_channel
        )


@bot.tree.command(name=f"{BOT_PREFIX}listcooldownplayers")
async def bot_lookup_cooldown_players(interaction: discord.Interaction):
    """List players on cooldown"""
    if await bot_functions.command_is_enabled(database=db, interaction=interaction):
        await bot_functions.show_list_cooldown(database=db, interaction=interaction)


#####################
### Team Commands ###
#####################


@bot.tree.command(name=f"{BOT_PREFIX}lookupteam")
async def bot_lookup_team(interaction: discord.Interaction, team_name: str = None):
    """Lookup a Team by name"""
    if await bot_functions.command_is_enabled(database=db, interaction=interaction):
        await bot_functions.show_team_details(
            database=db, interaction=interaction, team_name=team_name
        )


@bot.tree.command(name=f"{BOT_PREFIX}teamcreate")
async def bot_team_create(interaction: discord.Interaction, team_name: str):
    """Create a new Team"""
    if await bot_functions.command_is_enabled(database=db, interaction=interaction):
        log_channel = await discord_helpers.get_log_channel(guild=interaction.guild)
        await bot_functions.team_create(
            database=db,
            interaction=interaction,
            team_name=team_name,
            log_channel=log_channel,
        )


@bot.tree.command(name=f"{BOT_PREFIX}teamplayeradd")
async def bot_team_invite_offer(
    interaction: discord.Interaction, player_name: str = None, discord_id: str = None
):
    """Invite a player to join your Team"""
    if await bot_functions.command_is_enabled(database=db, interaction=interaction):
        await bot_functions.team_player_invite(
            database=db,
            interaction=interaction,
            player_name=player_name,
            player_discord_id=discord_id,
        )


@bot.tree.command(name=f"{BOT_PREFIX}teaminviteaccept")
async def bot_team_invite_accept(interaction: discord.Interaction):
    """Accept an invite to join a Team"""
    if await bot_functions.command_is_enabled(database=db, interaction=interaction):
        log_channel = await discord_helpers.get_log_channel(guild=interaction.guild)
        await bot_functions.team_player_accept(
            database=db, interaction=interaction, log_channel=log_channel
        )


@bot.tree.command(name=f"{BOT_PREFIX}teamplayerkick")
async def bot_team_player_remove(interaction: discord.Interaction, player_name: str):
    """Remove a player from your Team"""
    if await bot_functions.command_is_enabled(database=db, interaction=interaction):
        log_channel = await discord_helpers.get_log_channel(guild=interaction.guild)
        await bot_functions.team_player_remove(
            database=db,
            interaction=interaction,
            player_name=player_name,
            log_channel=log_channel,
        )


@bot.tree.command(name=f"{BOT_PREFIX}teamplayerpromote")
async def bot_team_player_promote(interaction: discord.Interaction, player_name: str):
    """Promote a player to Team Co-Captain"""
    if await bot_functions.command_is_enabled(database=db, interaction=interaction):
        log_channel = await discord_helpers.get_log_channel(guild=interaction.guild)
        await bot_functions.team_cocaptain_promote(
            database=db,
            interaction=interaction,
            player_name=player_name,
            log_channel=log_channel,
        )


@bot.tree.command(name=f"{BOT_PREFIX}teamplayerdemote")
async def bot_team_player_demote(interaction: discord.Interaction, player_name: str):
    """Demote a player from Team Co-Captain"""
    if await bot_functions.command_is_enabled(database=db, interaction=interaction):
        log_channel = await discord_helpers.get_log_channel(guild=interaction.guild)
        await bot_functions.team_cocaptain_demote(
            database=db,
            interaction=interaction,
            player_name=player_name,
            log_channel=log_channel,
        )


@bot.tree.command(name=f"{BOT_PREFIX}teamleave")
async def bot_team_leave(interaction: discord.Interaction):
    """Leave your current Team"""
    if await bot_functions.command_is_enabled(database=db, interaction=interaction):
        log_channel = await discord_helpers.get_log_channel(guild=interaction.guild)
        await bot_functions.team_player_leave(
            database=db, interaction=interaction, log_channel=log_channel
        )


@bot.tree.command(name=f"{BOT_PREFIX}teamdisband")
async def bot_team_disband(interaction: discord.Interaction):
    """Disband your Team"""
    if await bot_functions.command_is_enabled(database=db, interaction=interaction):
        log_channel = await discord_helpers.get_log_channel(guild=interaction.guild)
        await bot_functions.team_disband(
            database=db, interaction=interaction, log_channel=log_channel
        )


######################
### Match Commands ###
######################


@bot.tree.command(name=f"{BOT_PREFIX}matchdatepropose")
async def bot_match_propose(
    interaction: discord.Interaction, match_type: str, opponent_name: str, date: str
):
    """Propose a Match with another Team"""
    if await bot_functions.command_is_enabled(database=db, interaction=interaction):
        await bot_functions.match_invite(
            database=db,
            interaction=interaction,
            match_type=match_type,
            opposing_team_name=opponent_name,
            date_time=date,
        )


@bot.tree.command(name=f"{BOT_PREFIX}matchdateaccept")
async def bot_match_accept(
    interaction: discord.Interaction, match_invite_id: str = None
):
    """Accept a Match with another Team"""
    if await bot_functions.command_is_enabled(database=db, interaction=interaction):
        log_channel = await discord_helpers.get_log_channel(guild=interaction.guild)
        await bot_functions.match_accept(
            db,
            database=db,
            interaction=interaction,
            match_invite_id=match_invite_id,
            log_channel=log_channel,
        )


@bot.tree.command(name=f"{BOT_PREFIX}matchresultpropose")
async def bot_match_result_offer(
    interaction: discord.Interaction,
    match_type: str,
    opponent_name: str,
    outcome: str,
    round_1_us: int,
    round_1_them: int,
    round_2_us: int,
    round_2_them: int,
    round_3_us: int = None,
    round_3_them: int = None,
):
    """Propose a Match Result with another Team"""
    if await bot_functions.command_is_enabled(database=db, interaction=interaction):
        scores = [
            (round_1_us, round_1_them),
            (round_2_us, round_2_them),
            (round_3_us, round_3_them),
        ]
        await bot_functions.match_result_invite(
            db,
            database=db,
            interaction=interaction,
            match_type=match_type,
            opposing_team_name=opponent_name,
            scores=scores,
            outcome=outcome,
        )


@bot.tree.command(name=f"{BOT_PREFIX}matchresultaccept")
async def bot_match_result_accept(interaction: discord.Interaction):
    """Accept a Match Result with another Team"""
    if await bot_functions.command_is_enabled(database=db, interaction=interaction):
        log_channel = await discord_helpers.get_log_channel(guild=interaction.guild)
        await bot_functions.match_result_accept(
            db, database=db, interaction=interaction, log_channel=log_channel
        )


###^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^###
###                                          Bot Commands End                                                       ###
#######################################################################################################################


### Run Bot ###
bot.run(DISCORD_TOKEN)
