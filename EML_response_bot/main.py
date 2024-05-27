import discord
import os
from discord import app_commands
from discord.ext import commands
from typing import Optional
from dotenv import load_dotenv, dotenv_values

load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.members = True
intents.message_content = True  # Enable the message content intent


# Set case_insensitive to True
bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())


@bot.event
async def on_ready():
    print(f"IM HERE!")
    try:
        synced = await bot.tree.sync()
        print(f"synced {len(synced)} command(s)")
    except Exception as e:
        print(e)


@bot.tree.command(name="help")
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
        "`/leaguerules`: Display league rules.\n"
        "`/server_coc`: Display server Code of Conduct.\n"
        "`/ticket`: Display ticket information.\n"
        "`/support`: Display support information.\n"
        "`/staffapp`: Display staff application link.\n"
        "`/calendar`: Display the league calendar.\n"
        "`/eml_actionlist`: Display the EML action list.\n"
        "`/rolelookup <role>`: List members with a specific role."
    )

    await interaction.response.send_message(help_message)


@bot.tree.command(name="ranks")
async def ranks(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://echomasterleague.com/team-rankings-2/"
    )


@bot.tree.command(name="matches")
async def matches(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://echomasterleague.com/current-week-matches-and-results/"
    )


@bot.tree.command(name="rosters")
async def rosters(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://docs.google.com/spreadsheets/d/13vcfXkCejl9I4dtlA9ZI19dHGYh7aWIQXUU5MWhpYt0/edit?usp=sharing"
    )


@bot.tree.command(name="registration")
async def registration(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://echomasterleague.com/registrations/"
    )


@bot.tree.command(name="website")
async def website(interaction: discord.Interaction):
    await interaction.response.send_message(f"https://echomasterleague.com/")


@bot.tree.command(name="leaguerules")
async def leaguerules(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://echomasterleague.com/eml-league-rules/"
    )


@bot.tree.command(name="coc")
async def coc(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://discord.com/channels/1182380144887865406/1182380146506866823"
    )


@bot.tree.command(name="ticket")
async def ticket(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://discord.com/channels/1182380144887865406/1182380148436242475"
    )


@bot.tree.command(name="support")
async def support(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://discord.com/channels/1182380144887865406/1182380148436242476"
    )


@bot.tree.command(name="staffapp")
async def staffapp(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://echomasterleague.com/staff-application/"
    )


@bot.tree.command(name="calendar")
async def calendar(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://cdn.discordapp.com/attachments/1182380149468045354/1195235539289391114/Untitled401_20240111221722.png?ex=65b340d6&is=65a0cbd6&hm=d3d4ca3e5c16c9ef471c47782a4449698609cbb1ef1faf5ec70b9a1f570e98a8&"
    )


@bot.tree.command(name="ap")
async def ap(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://docs.google.com/spreadsheets/d/e/2PACX-1vSJmIGHxYlgMAy2Wvlz-pSx27iDTjBdzQbe7BCSu6qXCHk1kBTxwDJu0yAQuy0Msm3KLnIY2MwvMC8t/pubhtml"
    )


@bot.tree.command(name="actionlist")
async def actionlist(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"https://docs.google.com/spreadsheets/d/e/2PACX-1vRhkQIBw9ETybdGNVggWnAf9ueizzDMc0lbKcsDPQsD6c1jDd8p8u8OUwl5gdcR2M14KmCV6-eF03p4/pubhtml"
    )


@bot.tree.command(name="loungereport")
async def loungereport(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Gameplay violations such as halfcycling, cheat engine, etc. need to reported with evidence in a ticket to the Echo VR Lounge. Any action taken by EVRL will be considered for action by the EML AP system. https://discord.gg/echo-combat-lounge-779349159852769310"
    )


@bot.tree.command(name="rolelookup")
async def rolelookup(
    interaction: discord.Interaction,
    role_input1: str,
    role_input2: Optional[str] = None,
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


Token = os.environ.get("TOKEN")

# Run the bot with the token
bot.run(Token)
