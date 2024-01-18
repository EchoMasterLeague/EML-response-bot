import discord
import os
from discord import app_commands
from discord.ext import commands
from discord import Embed
from typing import Optional
from dotenv import load_dotenv, dotenv_values

load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.members = True
intents.message_content = True  # Enable the message content intent


# Set case_insensitive to True
bot = commands.Bot(command_prefix=".", intents = discord.Intents.all())

@bot.event
async def on_ready():
    print(f'IM HERE!')
    try:
        synced = await bot.tree.sync()
        print(f"synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

@bot.tree.command(name='help')
async def help_command(interaction: discord.Interaction):
    embed = Embed(title="Echo Master League Commands",
                  description="Here are some useful commands in Echo Master League Discord server:",
                  color=0x3498db)  # You can customize the color code

    # Add fields for each command
    embed.add_field(name="/ranks", value="Check the latest EML team rankings.", inline=False)
    embed.add_field(name="/matches", value="View the matches and results for the current week.", inline=False)
    embed.add_field(name="/rosters", value="Explore the rosters of teams in EML.", inline=False)
    embed.add_field(name="/registration", value="Register for Echo Master League and join the competition.", inline=False)
    embed.add_field(name="/website", value="Visit the official Echo Master League website for more information.", inline=False)
    embed.add_field(name="/league_rules", value="Read the rules and guidelines for Echo Master League.", inline=False)
    embed.add_field(name="/server_coc", value="Review the Code of Conduct for the EML Discord server.", inline=False)
    embed.add_field(name="/ticket", value="Submit a ticket for assistance, to report an issue, or to schedule your matches.", inline=False)
    embed.add_field(name="/support", value="Visit the support channel for assistance in the EML Discord server.", inline=False)
    embed.add_field(name="/staff_app", value="Apply to become part of EML Staff.", inline=False)
    embed.add_field(name="/calendar", value="View the EML calendar.", inline=False)
    embed.add_field(name="/ap", value="View the EML AP System.", inline=False)
    embed.add_field(name="/action_list", value="View the EML Action List.", inline=False)
    embed.add_field(name="/lounge_report", value="Report gameplay violations in the Echo VR Lounge.", inline=False)
    embed.add_field(name="/list_members", value="List members with specified roles.", inline=False)

    await interaction.response.send_message(embed=embed)
  

@bot.tree.command(name='ranks')
async def ranks(interaction: discord.Interaction):
      embed = Embed(title="EML Team Rankings",
                    description="Check the latest Echo Master League team rankings.",
                    url="https://echomasterleague.com/team-rankings-2/")

      await interaction.response.send_message(embed=embed)

@bot.tree.command(name='matches')
async def matches(interaction: discord.Interaction):
      embed = Embed(title="Current Week Matches and Results",
                    description="View the matches and results for the current week in Echo Master League.",
                    url="https://echomasterleague.com/current-week-matches-and-results/")

      await interaction.response.send_message(embed=embed)

@bot.tree.command(name='rosters')
async def rosters(interaction: discord.Interaction):
      embed = Embed(title="EML Team Rosters",
                    description="Explore the rosters of teams in Echo Master League.",
                    url="https://docs.google.com/spreadsheets/d/13vcfXkCejl9I4dtlA9ZI19dHGYh7aWIQXUU5MWhpYt0/edit?usp=sharing")

      await interaction.response.send_message(embed=embed)

@bot.tree.command(name='registration')
async def registration(interaction: discord.Interaction):
      embed = Embed(title="EML Registrations",
                    description="Register for Echo Master League and join the competition.",
                    url="https://echomasterleague.com/registrations/")

      await interaction.response.send_message(embed=embed)

@bot.tree.command(name='website')
async def website(interaction: discord.Interaction):
      embed = Embed(title="Echo Master League Website",
                    description="Visit the official Echo Master League website for more information.",
                    url="https://echomasterleague.com/")

      await interaction.response.send_message(embed=embed)

@bot.tree.command(name='league_rules')
async def league_rules(interaction: discord.Interaction):
      embed = Embed(title="EML League Rules",
                    description="Read the rules and guidelines for Echo Master League.",
                    url="https://echomasterleague.com/eml-league-rules/")

      await interaction.response.send_message(embed=embed)

@bot.tree.command(name='server_coc')
async def server_coc(interaction: discord.Interaction):
      embed = Embed(title="Discord Server Code of Conduct",
                    description="Review the Code of Conduct for the Echo Master League Discord server.",
                    url="https://discord.com/channels/1182380144887865406/1182380146506866823")

      await interaction.response.send_message(embed=embed)

@bot.tree.command(name='ticket')
async def ticket(interaction: discord.Interaction):
      embed = Embed(title="Ticket Submission",
                    description="Submit a ticket for assistance, to report an issue, or to schedule your matches.",
                    url="https://discord.com/channels/1182380144887865406/1182380148436242475")

      await interaction.response.send_message(embed=embed)

@bot.tree.command(name='support')
async def support(interaction: discord.Interaction):
      embed = Embed(title="Support Channel",
                    description="Visit the support channel for assistance in the Echo Master League Discord server.",
                    url="https://discord.com/channels/1182380144887865406/1182380148436242476")

      await interaction.response.send_message(embed=embed)

@bot.tree.command(name='staff_app')
async def staff_app(interaction: discord.Interaction):
      embed = Embed(title="Staff Application",
                    description="Apply to become part of EML Staff",
                    url="https://echomasterleague.com/staff-application/")

      await interaction.response.send_message(embed=embed)


@bot.tree.command(name='calendar')
async def staff_app(interaction: discord.Interaction):
    await interaction.response.send_message(f"https://cdn.discordapp.com/attachments/1182380149468045354/1195235539289391114/Untitled401_20240111221722.png?ex=65b340d6&is=65a0cbd6&hm=ef1faf5ec70b9a1f570e98a8&")

@bot.tree.command(name='ap')
async def ap(interaction: discord.Interaction):
      embed = Embed(title="EML AP System",
                    description="View the AP System.",
                    url="https://docs.google.com/spreadsheets/d/e/2PACX-1vSJmIGHxYlgMAy2Wvlz-pSx27iDTjBdzQbe7BCSu6qXCHk1kBTxwDJu0yAQuy0Msm3KLnIY2MwvMC8t/pubhtml")

      await interaction.response.send_message(embed=embed)

@bot.tree.command(name='action_list')
async def action_list(interaction: discord.Interaction):
      embed = Embed(title="EML Action List",
                    description="View the EML Action List.",
                    url="https://docs.google.com/spreadsheets/d/e/2PACX-1vRhkQIBw9ETybdGNVggWnAf9ueizzDMc0lbKcsDPQsD6c1jDd8p8u8OUwl5gdcR2M14KmCV6-eF03p4/pubhtml")

      await interaction.response.send_message(embed=embed)

@bot.tree.command(name='lounge_report')
async def lounge_report(interaction: discord.Interaction):
      message_content = (
          "Gameplay violations such as halfcycling, cheat engine, etc. need to be reported with evidence "
          "in a ticket to the Echo VR Lounge. Any action taken by EVRL will be considered for action by the EML AP system. "
          "[Echo VR Lounge Discord](https://discord.gg/echo-combat-lounge-779349159852769310)"
      )
      await interaction.response.send_message(content=message_content)


@bot.tree.command(name='list_members')
async def list_members(interaction: discord.Interaction, role_input1: str, role_input2: Optional[str] = None):
    # Get the guild from the interaction
    guild = interaction.guild

    if guild:
        # Get role based on the provided role_input1 (case-insensitive)
        role1 = discord.utils.get(guild.roles, name=role_input1, case_insensitive=True) or discord.utils.get(guild.roles, mention=role_input1)

        # If role_input2 is provided, get the role based on it (case-insensitive)
        role2 = discord.utils.get(guild.roles, name=role_input2, case_insensitive=True) or discord.utils.get(guild.roles, mention=role_input2) if role_input2 else None

        if role1:
            # Print some debug information
            print(f"Roles found: {role1.name}, {role1.id}, {role2.name if role2 else None}, {role2.id if role2 else None}")

            # Get members with specified roles (case-insensitive comparison)
            if role2:
                members_with_roles = [member.display_name for member in guild.members if all(role in member.roles for role in (role1, role2))]
            else:
                members_with_roles = [member.display_name for member in guild.members if role1 in member.roles]

            if members_with_roles:
                await interaction.response.send_message(f"Members with {role1.mention} role{' and ' + role2.mention if role2 else ''}: {', '.join(members_with_roles)}", ephemeral=True)
            else:
                await interaction.response.send_message(f"No members found with {role1.mention} role{' and ' + role2.mention if role2 else ''}.", ephemeral=True)
        else:
            await interaction.response.send_message("Role not found.", ephemeral=True)
    else:
        await interaction.response.send_message("Error: Guild not found.", ephemeral=True)


Token = os.environ.get("TOKEN")

# Run the bot with the token
bot.run(Token)
