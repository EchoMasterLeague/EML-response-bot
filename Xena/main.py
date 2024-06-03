from bot_functions.manage_commands import ManageCommands
from bot_functions.manage_players import ManagePlayers
from bot_functions.manage_teams import ManageTeams
from bot_functions.manage_matches import ManageMatches
from bot_functions.manage_system import ManageSystem
from database.database_core import CoreDatabase
from database.database_full import FullDatabase
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
database = FullDatabase(database_core)

# Bot Functions
manage_players = ManagePlayers(database)
manage_teams = ManageTeams(database)
manage_commands = ManageCommands(database)
manage_matches = ManageMatches(database)
manage_system = ManageSystem(database)

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

#######################
### System Commands ###
#######################


@bot.tree.command(name=f"{BOT_PREFIX}zdebugdbqueue")
async def bot_z_debug_db_queue(interaction: discord.Interaction):
    """Debug the pending writes"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_system.list_pending_writes(interaction)


@bot.tree.command(name=f"{BOT_PREFIX}zdebugdbcache")
async def bot_z_debug_db_cache(interaction: discord.Interaction):
    """Debug the local cache"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_system.list_local_cache(interaction)


#######################
### Player Commands ###
#######################


@bot.tree.command(name=f"{BOT_PREFIX}lookupplayer")
async def bot_lookup_player(
    interaction: discord.Interaction, player_name: str = None, discord_id: str = None
):
    """Lookup a Player by name or Discord ID"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_players.get_player_details(interaction, player_name, discord_id)


@bot.tree.command(name=f"{BOT_PREFIX}playerregister")
async def bot_player_register(interaction: discord.Interaction):
    """Register to become a Player"""
    if await manage_commands.is_command_enabled(interaction):
        log_channel = await discord_helpers.get_log_channel(interaction.guild)
        await manage_players.register_player(
            interaction=interaction, log_channel=log_channel
        )


@bot.tree.command(name=f"{BOT_PREFIX}playerunregister")
async def bot_player_unregister(interaction: discord.Interaction):
    """Unregister as a Player"""
    if await manage_commands.is_command_enabled(interaction):
        log_channel = await discord_helpers.get_log_channel(interaction.guild)
        await manage_players.unregister_player(
            interaction=interaction, log_channel=log_channel
        )


@bot.tree.command(name=f"{BOT_PREFIX}listcooldownplayers")
async def bot_lookup_cooldown_players(interaction: discord.Interaction):
    """List players on cooldown"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_players.get_cooldown_players(interaction)


#####################
### Team Commands ###
#####################


@bot.tree.command(name=f"{BOT_PREFIX}lookupteam")
async def bot_lookup_team(interaction: discord.Interaction, team_name: str = None):
    """Lookup a Team by name"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_teams.get_team_details(interaction, team_name)


@bot.tree.command(name=f"{BOT_PREFIX}teamcreate")
async def bot_team_create(interaction: discord.Interaction, team_name: str):
    """Create a new Team"""
    if await manage_commands.is_command_enabled(interaction):
        log_channel = await discord_helpers.get_log_channel(interaction.guild)
        await manage_teams.create_team(
            interaction=interaction, team_name=team_name, log_channel=log_channel
        )


@bot.tree.command(name=f"{BOT_PREFIX}teamplayeradd")
async def bot_team_invite_offer(
    interaction: discord.Interaction, player_name: str = None, discord_id: str = None
):
    """Invite a player to join your Team"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_teams.invite_player_to_team(interaction, player_name, discord_id)


@bot.tree.command(name=f"{BOT_PREFIX}teaminviteaccept")
async def bot_team_invite_accept(interaction: discord.Interaction):
    """Accept an invite to join a Team"""
    if await manage_commands.is_command_enabled(interaction):
        log_channel = await discord_helpers.get_log_channel(interaction.guild)
        await manage_teams.accept_invite(
            interaction=interaction, log_channel=log_channel
        )


@bot.tree.command(name=f"{BOT_PREFIX}teamplayerkick")
async def bot_team_player_remove(interaction: discord.Interaction, player_name: str):
    """Remove a player from your Team"""
    if await manage_commands.is_command_enabled(interaction):
        log_channel = await discord_helpers.get_log_channel(interaction.guild)
        await manage_teams.remove_player_from_team(
            interaction=interaction, player_name=player_name, log_channel=log_channel
        )


@bot.tree.command(name=f"{BOT_PREFIX}teamplayerpromote")
async def bot_team_player_promote(interaction: discord.Interaction, player_name: str):
    """Promote a player to Team Co-Captain"""
    if await manage_commands.is_command_enabled(interaction):
        log_channel = await discord_helpers.get_log_channel(interaction.guild)
        await manage_teams.promote_player_to_co_captain(
            interaction=interaction, player_name=player_name, log_channel=log_channel
        )


@bot.tree.command(name=f"{BOT_PREFIX}teamplayerdemote")
async def bot_team_player_demote(interaction: discord.Interaction, player_name: str):
    """Demote a player from Team Co-Captain"""
    if await manage_commands.is_command_enabled(interaction):
        log_channel = await discord_helpers.get_log_channel(interaction.guild)
        await manage_teams.demote_player_from_co_captain(
            interaction=interaction, player_name=player_name, log_channel=log_channel
        )


@bot.tree.command(name=f"{BOT_PREFIX}teamleave")
async def bot_team_leave(interaction: discord.Interaction):
    """Leave your current Team"""
    if await manage_commands.is_command_enabled(interaction):
        log_channel = await discord_helpers.get_log_channel(interaction.guild)
        await manage_teams.leave_team(interaction=interaction, log_channel=log_channel)


@bot.tree.command(name=f"{BOT_PREFIX}teamdisband")
async def bot_team_disband(interaction: discord.Interaction):
    """Disband your Team"""
    if await manage_commands.is_command_enabled(interaction):
        log_channel = await discord_helpers.get_log_channel(interaction.guild)
        await manage_teams.disband_team(
            interaction=interaction, log_channel=log_channel
        )


######################
### Match Commands ###
######################


@bot.tree.command(name=f"{BOT_PREFIX}matchdatepropose")
async def bot_match_propose(
    interaction: discord.Interaction, match_type: str, opponent_name: str, date: str
):
    """Propose a Match with another Team"""
    if await manage_commands.is_command_enabled(interaction):
        await manage_matches.send_match_invite(
            interaction, match_type, opponent_name, date
        )


@bot.tree.command(name=f"{BOT_PREFIX}matchdateaccept")
async def bot_match_accept(
    interaction: discord.Interaction, match_invite_id: str = None
):
    """Accept a Match with another Team"""
    if await manage_commands.is_command_enabled(interaction):
        log_channel = await discord_helpers.get_log_channel(interaction.guild)
        await manage_matches.accept_match_invite(
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
    if await manage_commands.is_command_enabled(interaction):
        scores = [
            (round_1_us, round_1_them),
            (round_2_us, round_2_them),
            (round_3_us, round_3_them),
        ]
        await manage_matches.send_result_invite(
            interaction=interaction,
            match_type=match_type,
            opposing_team_name=opponent_name,
            scores=scores,
            outcome=outcome,
        )


@bot.tree.command(name=f"{BOT_PREFIX}matchresultaccept")
async def bot_match_result_accept(interaction: discord.Interaction):
    """Accept a Match Result with another Team"""
    if await manage_commands.is_command_enabled(interaction):
        log_channel = await discord_helpers.get_log_channel(interaction.guild)
        await manage_matches.accept_result_invite(
            interaction=interaction, log_channel=log_channel
        )


#########################
### Original Commands ###
#########################


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
async def rolelookup(
    interaction: discord.Interaction,
    role_input1: str,
    role_input2: str = None,
):
    # Get the guild from the interaction
    guild = interaction.guild

    if guild:
        # Get role based on the provided role_input1 (case-insensitive)
        role1 = discord.utils.get(
            guild.roles, name=role_input1, case_insensitive=True
        ) or discord.utils.get(guild.roles, mention=role_input1)

        # If role_input2 is provided, get the role based on it (case-insensitive)
        role2 = (
            discord.utils.get(guild.roles, name=role_input2, case_insensitive=True)
            or discord.utils.get(guild.roles, mention=role_input2)
            if role_input2
            else None
        )

        if role1:
            # Print some debug information
            print(
                f"Roles found: {role1.name}, {role1.id}, {role2.name if role2 else None}, {role2.id if role2 else None}"
            )

            # Get members with specified roles (case-insensitive comparison)
            if role2:
                members_with_roles = [
                    member.display_name
                    for member in guild.members
                    if all(role in member.roles for role in (role1, role2))
                ]
            else:
                members_with_roles = [
                    member.display_name
                    for member in guild.members
                    if role1 in member.roles
                ]

            if members_with_roles:
                await interaction.response.send_message(
                    f"Members with {role1.mention} role{' and ' + role2.mention if role2 else ''}: {', '.join(members_with_roles)}",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    f"No members found with {role1.mention} role{' and ' + role2.mention if role2 else ''}.",
                    ephemeral=True,
                )
        else:
            await interaction.response.send_message("Role not found.", ephemeral=True)
    else:
        await interaction.response.send_message(
            "Error: Guild not found.", ephemeral=True
        )


###^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^###
###                                          Bot Commands End                                                       ###
#######################################################################################################################


### Run Bot ###
bot.run(DISCORD_TOKEN)
