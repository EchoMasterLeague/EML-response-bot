import discord
import os
from discord import app_commands
from discord.ext import commands
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

@bot.tree.command(name='ranks')
async def ranks(interaction: discord.Interaction):
    await interaction.response.send_message(f"https://echomasterleague.com/team-rankings-2/")

@bot.tree.command(name='matches')
async def matches(interaction: discord.Interaction):
    await interaction.response.send_message(f"https://echomasterleague.com/team-matches-and-results/")

@bot.tree.command(name='rosters')
async def rosters(interaction: discord.Interaction):
    await interaction.response.send_message(f"https://docs.google.com/spreadsheets/d/13vcfXkCejl9I4dtlA9ZI19dHGYh7aWIQXUU5MWhpYt0/edit?usp=sharing")

@bot.tree.command(name='registration')
async def registration(interaction: discord.Interaction):
    await interaction.response.send_message(f"https://echomasterleague.com/registrations/")

@bot.tree.command(name='website')
async def website(interaction: discord.Interaction):
    await interaction.response.send_message(f"https://echomasterleague.com/")

@bot.tree.command(name='league_rules')
async def league_rules(interaction: discord.Interaction):
    await interaction.response.send_message(f"https://echomasterleague.com/eml-league-rules/")

@bot.tree.command(name='server_coc')
async def server_coc(interaction: discord.Interaction):
    await interaction.response.send_message(f"https://discord.com/channels/1182380144887865406/1182380146506866823")

@bot.tree.command(name='ticket')
async def ticket(interaction: discord.Interaction):
    await interaction.response.send_message(f"https://discord.com/channels/1182380144887865406/1182380148436242475")

@bot.tree.command(name='support')
async def support(interaction: discord.Interaction):
    await interaction.response.send_message(f"https://discord.com/channels/1182380144887865406/1182380148436242476")

@bot.tree.command(name='list_members')
async def list_members(interaction: discord.Interaction, role_input: str):
    # Get role based on the provided role_input (case-insensitive)
    # Get the guild from the interaction
    guild = interaction.guild

    if guild:

    # Get role based on the provided role_input (case-insensitive)
        role = discord.utils.get(guild.roles, name=role_input, case_insensitive=True) or discord.utils.get(guild.roles, mention=role_input)
    if role:
        # Print some debug information
        print(f"Role found: {role.name}, {role.id}")

        # Get all members with the specified role (case-insensitive comparison)
        members_with_role = [member.name for member in role.members]

        if members_with_role:
            await interaction.response.send_message(f"Members with the role {role.mention}: {', '.join(members_with_role)}",ephemeral=True)
        else:
            await interaction.response.send_message(f"No members found with the role {role.mention}.",ephemeral=True)
        await interaction.response.send_message("Role {role_input} not found.")
    else:
        await interaction.response.send_message("Error: Guild not found.",ephemeral=True)
      
Token = os.environ.get("TOKEN")

# Run the bot with the token
bot.run(Token)

