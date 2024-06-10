from database.database_core import CoreDatabase
from database.database_full import FullDatabase
import bot_commands
import bot_helpers
import constants
import discord
import discord.ext.commands as commands
import dotenv
import gspread
import os

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
SPREADSHEET_URL = os.environ.get("SPREADSHEET_URL")
SPREADSHEET_URL = (
    SPREADSHEET_URL if SPREADSHEET_URL else constants.LINK_DB_SPREADSHEET_URL
)

# Google Sheets "Database"
# gs_client = gspread.service_account(GOOGLE_CREDENTIALS_FILE, http_client=gspread.BackOffHTTPClient)  # For 429 backoff, but breaks on 403
gs_client = gspread.service_account(GOOGLE_CREDENTIALS_FILE)
database_core = CoreDatabase(gs_client, SPREADSHEET_URL)
db = FullDatabase(database_core)

# Discord Intents
intents = discord.Intents.default()
intents.messages = True
intents.members = True
intents.message_content = True

# Discord Bot
# bot = commands.Bot(command_prefix=".", intents=intents)
bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())
bot_state = {"synced": False}


@bot.event
async def on_ready():
    """Event triggered when the bot is ready."""
    if bot_state["synced"]:
        return
    bot_state["synced"] = True
    # Sync Commands
    if GUILD_ID and False:
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
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(
        database=db, interaction=interaction, skip_channel=True
    ):
        # f"`/{BOT_PREFIX}{constants.COMMAND_REGISTRATION}`: Gives a link to the website NA Team Registration Form\n"
        await interaction.response.send_message(
            ephemeral=True,
            content="\n".join(
                [
                    f"**Help**\n",
                    f"`/{BOT_PREFIX}{constants.COMMAND_HELP}`: Show this message",
                    f"`/{BOT_PREFIX}{constants.COMMAND_COMMANDS}`: Link command reference",
                    f"`/{BOT_PREFIX}{constants.COMMAND_INSTRUCTIONS}`: Link to bot guide",
                    f"`/{BOT_PREFIX}{constants.COMMAND_SUPPORT}`: Link to #league-faq",
                    f"`/{BOT_PREFIX}{constants.COMMAND_TICKET}`: Link to ticketing in Echo Master League",
                    f"**Rules**",
                    f"`/{BOT_PREFIX}{constants.COMMAND_COC}`: Link to the Code of Conduct",
                    f"`/{BOT_PREFIX}{constants.COMMAND_LEAGUE_RULES}`: Link to League Rules",
                    f"`/{BOT_PREFIX}{constants.COMMAND_AP}`: Link to the Accumulated Points system",
                    f"**Violations**",
                    f"`/{BOT_PREFIX}{constants.COMMAND_LOUNGE_REPORT}`: Link to ticketing in Echo VR Lounge",
                    f"`/{BOT_PREFIX}{constants.COMMAND_ACTION_LIST}`: Link to the violator action list",
                    f"**League Info**",
                    f"`/{BOT_PREFIX}{constants.COMMAND_WEBSITE}`: Link to EML website",
                    f"`/{BOT_PREFIX}{constants.COMMAND_STAFF_APP}`: Link to EML staff application",
                    f"**Season Info**",
                    f"`/{BOT_PREFIX}{constants.COMMAND_CALENDAR_EU}`: Show EU League Calendar",
                    f"`/{BOT_PREFIX}{constants.COMMAND_CALENDAR_NA}`: Show NA League Calendar",
                    f"`/{BOT_PREFIX}{constants.COMMAND_MATCHES}`: Link to upcoming matches list",
                    f"`/{BOT_PREFIX}{constants.COMMAND_RANKS}`: Link to team rankings",
                    f"`/{BOT_PREFIX}{constants.COMMAND_ROSTERS}`: Link to roster",
                    f"**League Management Commands**",
                    f"**Players**",
                    f"`/{BOT_PREFIX}{constants.COMMAND_PLAYERREGISTER}`: Register into the League",
                    f"`/{BOT_PREFIX}{constants.COMMAND_PLAYERUNREGISTER}`: Unregister from the League",
                    f"**Teams**",
                    f"`/{BOT_PREFIX}{constants.COMMAND_TEAMINVITEACCEPT}`: Join a team",
                    f"`/{BOT_PREFIX}{constants.COMMAND_TEAMCREATE}`: Create year own team",
                    f"`/{BOT_PREFIX}{constants.COMMAND_TEAMPLAYERADD}`: Invite a player to join your team",
                    f"`/{BOT_PREFIX}{constants.COMMAND_TEAMLEAVE}`: Leave your team",
                    f"`/{BOT_PREFIX}{constants.COMMAND_TEAMDISBAND}`: Disband your team",
                    f"`/{BOT_PREFIX}{constants.COMMAND_TEAMPLAYERKICK}`: Remove teammate from your team",
                    f"`/{BOT_PREFIX}{constants.COMMAND_TEAMPLAYERPROMOTE}`: Specify Co-Captain of your team",
                    f"`/{BOT_PREFIX}{constants.COMMAND_TEAMPLAYERDEMOTE}`: Remove Co-Captain role from your teammate",
                    f"**Matches**",
                    f"`/{BOT_PREFIX}{constants.COMMAND_MATCHDATEACCEPT}`: Accept match date and time proposed by another team",
                    f"`/{BOT_PREFIX}{constants.COMMAND_MATCHRESULTACCEPT}`: Accept match results proposed by another team",
                    f"`/{BOT_PREFIX}{constants.COMMAND_MATCHDATEPROPOSE}`: Propose match date and time to another team",
                    f"`/{BOT_PREFIX}{constants.COMMAND_MATCHRESULTPROPOSE}`: Propose match results to another team",
                    f"**Lookup**",
                    f"`/{BOT_PREFIX}{constants.COMMAND_LOOKUPPLAYER}`: Show player details",
                    f"`/{BOT_PREFIX}{constants.COMMAND_LOOKUPTEAM}`: Show team details",
                    f"`/{BOT_PREFIX}{constants.COMMAND_LISTCOOLDOWNPLAYERS}`: Show players who recenly left a team",
                    f"`/{BOT_PREFIX}{constants.COMMAND_ROLELOOKUP}`: Show discord members with a specific role",
                    f"**Debug**",
                    f"`/{BOT_PREFIX}{constants.COMMAND_ZDEBUGDBCACHE}`: Show database cache pull timestamps",
                    f"`/{BOT_PREFIX}{constants.COMMAND_ZDEBUGDBQUEUE}`: Show database write queue",
                ]
            ),
        )


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_RANKS}")
async def ranks(interaction: discord.Interaction):
    """Link to Team Rankings"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(
        database=db, interaction=interaction, skip_channel=True
    ):
        link = constants.LINK_TEAM_RANKINGS
        await interaction.response.send_message(f"Team Rankings: {link}")


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_MATCHES}")
async def matches(interaction: discord.Interaction):
    """Link to upcoming Matches"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(
        database=db, interaction=interaction, skip_channel=True
    ):
        link = constants.LINK_LEAGUE_MATCHES
        await interaction.response.send_message(f"Upcoming Matches: {link}")


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_ROSTERS}")
async def rosters(interaction: discord.Interaction):
    """Link to League Roster"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(
        database=db, interaction=interaction, skip_channel=True
    ):
        link = constants.LINK_LEAGUE_ROSTER
        await interaction.response.send_message(f"Roster: {link}")


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_WEBSITE}")
async def website(interaction: discord.Interaction):
    """Link to EML Website"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(
        database=db, interaction=interaction, skip_channel=True
    ):
        link = constants.LINK_EML_WEBSITE
        await interaction.response.send_message(f"EML Website: {link}")


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_INSTRUCTIONS}")
async def website(interaction: discord.Interaction):
    """Link to Bot Instructions"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(
        database=db, interaction=interaction, skip_channel=True
    ):
        link = constants.LINK_BOT_INSTRUCTIONS
        await interaction.response.send_message(f"Bot Instructions: {link}")


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_COMMANDS}")
async def website(interaction: discord.Interaction):
    """Link to Command Reference"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(
        database=db, interaction=interaction, skip_channel=True
    ):
        link = constants.LINK_BOT_COMMANDS
        await interaction.response.send_message(f"Command Reference: {link}")


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_LEAGUE_RULES}")
async def leaguerules(interaction: discord.Interaction):
    """Link to EML League Rules"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(
        database=db, interaction=interaction, skip_channel=True
    ):
        link = constants.LINK_LEAGUE_RULES
        await interaction.response.send_message(f"League Rules: {link}")


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_COC}")
async def coc(interaction: discord.Interaction):
    """Link to EML Code of Conduct"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(
        database=db, interaction=interaction, skip_channel=True
    ):
        link = constants.LINK_DISCORD_CHANNEL_EML_COC
        await interaction.response.send_message(f"EML Code of Conduct: {link}")


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_TICKET}")
async def ticket(interaction: discord.Interaction):
    """Link to EML Tickets"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(
        database=db, interaction=interaction, skip_channel=True
    ):
        link = constants.LINK_DISCORD_CHANNEL_EML_TICKETS
        await interaction.response.send_message(f"EML Tickets: {link}")


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_SUPPORT}")
async def support(interaction: discord.Interaction):
    """Link to EML Support (FAQ)"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(
        database=db, interaction=interaction, skip_channel=True
    ):
        link = constants.LINK_DISCORD_CHANNEL_EML_SUPPORT
        await interaction.response.send_message(f"EML Support (FAQ): {link}")


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_STAFF_APP}")
async def staff_app(interaction: discord.Interaction):
    """Link to EML Staff Application"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(
        database=db, interaction=interaction, skip_channel=True
    ):
        link = constants.LINK_STAFF_APPLICATION
        await interaction.response.send_message(f"Staff Application: {link}")


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_CALENDAR_EU}")
async def staff_app(interaction: discord.Interaction):
    """Link to EU Calendar"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(
        database=db, interaction=interaction, skip_channel=True
    ):
        link = constants.LINK_CALENDAR_EU
        await interaction.response.send_message(f"**Europe**: [EU]({link})")


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_CALENDAR_NA}")
async def staff_app(interaction: discord.Interaction):
    """Link to NA Calendar"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(
        database=db, interaction=interaction, skip_channel=True
    ):
        link = constants.LINK_CALENDAR_NA
        await interaction.response.send_message(f"**North America**: [NA]({link})")


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_AP}")
async def ap(interaction: discord.Interaction):
    """Link to Accumulated Points"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(
        database=db, interaction=interaction, skip_channel=True
    ):
        link = constants.LINK_ACCUMULATED_POINTS
        await interaction.response.send_message(f"Accumlulated Points: {link}")


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_ACTION_LIST}")
async def action_list(interaction: discord.Interaction):
    """Link to Action List"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(
        database=db, interaction=interaction, skip_channel=True
    ):
        link = constants.LINK_ACTION_LIST
        await interaction.response.send_message(f"Action List: {link}")


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_LOUNGE_REPORT}")
async def lounge_report(interaction: discord.Interaction):
    """Link to Echo VR Lounge Reporting"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(
        database=db, interaction=interaction, skip_channel=True
    ):
        link_lounge = constants.LINK_ECHO_VR_LOUNGE
        link_report = constants.LINK_ECHO_VR_LOUNGE_TICKETS
        await interaction.response.send_message(
            f"**Echo VR Lounge Reporting**:\n"
            f"Gameplay violations such as halfcycling, cheat engine, etc. need to reported with evidence in a ticket to the Echo VR Lounge. Any action taken by EVRL will be considered for action by the EML AP system.\n\n"
            f"Ticket Channel: {link_report}\n"
            f"Echo VR Lounge: {link_lounge}\n"
        )


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_ROLELOOKUP}")
async def bot_rolelookup(
    interaction: discord.Interaction,
    role_input1: str,
    role_input2: str = None,
):
    """Show members with a specific role"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(
        database=db, interaction=interaction, skip_channel=True
    ):
        await bot_commands.show_role_members(
            interaction=interaction, role_input1=role_input1, role_input2=role_input2
        )


#######################
### System Commands ###
#######################


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_ZDEBUGDBQUEUE}")
async def bot_z_debug_db_queue(interaction: discord.Interaction):
    """Debug the pending writes"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(database=db, interaction=interaction):
        await bot_commands.system_list_writes(database=db, interaction=interaction)


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_ZDEBUGDBCACHE}")
async def bot_z_debug_db_cache(interaction: discord.Interaction):
    """Debug the local cache"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(database=db, interaction=interaction):
        await bot_commands.system_list_cache(database=db, interaction=interaction)


#######################
### Player Commands ###
#######################


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_LOOKUPPLAYER}")
async def bot_lookup_player(
    interaction: discord.Interaction,
    player: discord.Member,
):
    """Lookup a Player by name or Discord ID"""
    await bot_helpers.command_log(
        {**locals(), "player": f"{player.display_name}({player.id})"}
    )
    if await bot_helpers.command_is_enabled(database=db, interaction=interaction):
        await bot_commands.show_player_details(
            database=db,
            interaction=interaction,
            discord_member=player,
        )


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_PLAYERREGISTER}")
async def bot_player_register(interaction: discord.Interaction):
    """Register to become a Player"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(database=db, interaction=interaction):
        await bot_commands.player_register(database=db, interaction=interaction)


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_PLAYERUNREGISTER}")
async def bot_player_unregister(interaction: discord.Interaction):
    """Unregister as a Player"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(database=db, interaction=interaction):
        await bot_commands.player_unregister(database=db, interaction=interaction)


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_LISTCOOLDOWNPLAYERS}")
async def bot_lookup_cooldown_players(interaction: discord.Interaction):
    """List players on cooldown"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(database=db, interaction=interaction):
        await bot_commands.show_list_cooldown(database=db, interaction=interaction)


#####################
### Team Commands ###
#####################


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_LOOKUPTEAM}")
async def bot_lookup_team(interaction: discord.Interaction, team_name: str = None):
    """Lookup a Team by name"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(database=db, interaction=interaction):
        await bot_commands.show_team_details(
            database=db, interaction=interaction, team_name=team_name
        )


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_TEAMCREATE}")
async def bot_team_create(interaction: discord.Interaction, team_name: str):
    """Create a new Team"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(database=db, interaction=interaction):
        await bot_commands.team_create(
            database=db,
            interaction=interaction,
            team_name=team_name,
        )


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_TEAMPLAYERADD}")
async def bot_team_invite_offer(
    interaction: discord.Interaction, player: discord.Member
):
    """Invite a player to join your Team"""
    await bot_helpers.command_log(
        {**locals(), "player": f"{player.display_name}({player.id})"}
    )
    if await bot_helpers.command_is_enabled(database=db, interaction=interaction):
        await bot_commands.team_player_invite(
            database=db, interaction=interaction, discord_member=player
        )


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_TEAMINVITEACCEPT}")
async def bot_team_invite_accept(interaction: discord.Interaction):
    """Accept an invite to join a Team"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(database=db, interaction=interaction):
        await bot_commands.team_player_accept(database=db, interaction=interaction)


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_TEAMPLAYERKICK}")
async def bot_team_player_remove(
    interaction: discord.Interaction, player: discord.Member
):
    """Remove a player from your Team"""
    await bot_helpers.command_log(
        {**locals(), "player": f"{player.display_name}({player.id})"}
    )
    if await bot_helpers.command_is_enabled(database=db, interaction=interaction):
        await bot_commands.team_player_remove(
            database=db,
            interaction=interaction,
            discord_member=player,
        )


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_TEAMPLAYERPROMOTE}")
async def bot_team_player_promote(
    interaction: discord.Interaction, player: discord.Member
):
    """Promote a player to Team Co-Captain"""
    await bot_helpers.command_log(
        {**locals(), "player": f"{player.display_name}({player.id})"}
    )
    if await bot_helpers.command_is_enabled(database=db, interaction=interaction):
        await bot_commands.team_cocaptain_promote(
            database=db,
            interaction=interaction,
            discord_member=player,
        )


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_TEAMPLAYERDEMOTE}")
async def bot_team_player_demote(
    interaction: discord.Interaction, player: discord.Member
):
    """Demote a player from Team Co-Captain"""
    await bot_helpers.command_log(
        {**locals(), "player": f"{player.display_name}({player.id})"}
    )
    if await bot_helpers.command_is_enabled(database=db, interaction=interaction):
        await bot_commands.team_cocaptain_demote(
            database=db,
            interaction=interaction,
            discord_member=player,
        )


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_TEAMLEAVE}")
async def bot_team_leave(interaction: discord.Interaction):
    """Leave your current Team"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(database=db, interaction=interaction):
        await bot_commands.team_player_leave(database=db, interaction=interaction)


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_TEAMDISBAND}")
async def bot_team_disband(interaction: discord.Interaction):
    """Disband your Team"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(database=db, interaction=interaction):
        await bot_commands.team_disband(database=db, interaction=interaction)


######################
### Match Commands ###
######################


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_MATCHDATEPROPOSE}")
async def bot_match_propose(
    interaction: discord.Interaction, opponent: discord.Role, match_type: str, date: str
):
    """Propose a Match with another Team"""
    await bot_helpers.command_log({**locals(), "opponent": f"{opponent.name}"})
    if await bot_helpers.command_is_enabled(database=db, interaction=interaction):
        await bot_commands.match_invite(
            database=db,
            interaction=interaction,
            to_team_role=opponent,
            match_type=match_type,
            date_time=date,
        )


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_MATCHDATEACCEPT}")
async def bot_match_accept(interaction: discord.Interaction):
    """Accept a Match with another Team"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(database=db, interaction=interaction):
        await bot_commands.match_accept(database=db, interaction=interaction)


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_MATCHRESULTPROPOSE}")
async def bot_match_result_offer(
    interaction: discord.Interaction,
    opponent: discord.Role,
    match_type: str,
    outcome: str,
    round_1_us: int,
    round_1_them: int,
    round_2_us: int,
    round_2_them: int,
    round_3_us: int = None,
    round_3_them: int = None,
):
    """Propose a Match Result with another Team"""
    await bot_helpers.command_log({**locals(), "opponent": f"{opponent.name}"})
    if await bot_helpers.command_is_enabled(database=db, interaction=interaction):
        scores = [
            (round_1_us, round_1_them),
            (round_2_us, round_2_them),
            (round_3_us, round_3_them),
        ]
        await bot_commands.match_result_invite(
            database=db,
            interaction=interaction,
            to_team_role=opponent,
            match_type=match_type,
            outcome=outcome,
            scores=scores,
        )


@bot.tree.command(name=f"{BOT_PREFIX}{constants.COMMAND_MATCHRESULTACCEPT}")
async def bot_match_result_accept(interaction: discord.Interaction):
    """Accept a Match Result with another Team"""
    await bot_helpers.command_log({**locals()})
    if await bot_helpers.command_is_enabled(database=db, interaction=interaction):
        await bot_commands.match_result_accept(database=db, interaction=interaction)


###^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^###
###                                          Bot Commands End                                                       ###
#######################################################################################################################


### Run Bot ###
bot.run(DISCORD_TOKEN)
