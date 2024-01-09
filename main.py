import discord
import os
from discord.ext import commands
from dotenv import load_dotenv, dotenv_values

load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.members = True
intents.message_content = True  # Enable the message content intent

# Set case_insensitive to True
bot = commands.Bot(command_prefix=".", intents=intents, case_insensitive=True)


class CustomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='Ranks')
    async def ranks(self, ctx):
        await ctx.send("https://echomasterleague.com/team-rankings-2/")

    @commands.command(name='Matches')
    async def matches(self, ctx):
        await ctx.send("https://echomasterleague.com/team-matches-and-results/")

    @commands.command(name='Rosters')
    async def rosters(self, ctx):
        await ctx.send("https://docs.google.com/spreadsheets/d/13vcfXkCejl9I4dtlA9ZI19dHGYh7aWIQXUU5MWhpYt0/edit?usp=sharing")

    @commands.command(name='Registration')
    async def registration(self, ctx):
        await ctx.send("https://echomasterleague.com/registrations/")

    @commands.command(name='Website')
    async def website(self, ctx):
        await ctx.send("https://echomasterleague.com/")

    @commands.command(name='help!')
    async def help(self, ctx):
        await ctx.send("Commands: .Website    .League_rules    .Server_CoC    .Ranks    .Matches    .Rosters    .Registration    .Ticket   .Support    .list_members")

    @commands.command(name='League_rules')
    async def league_rules(self, ctx):
        await ctx.send("https://echomasterleague.com/eml-league-rules/")

    @commands.command(name='Server_CoC')
    async def server_coc(self, ctx):
        await ctx.send("https://discord.com/channels/1182380144887865406/1182380146506866823")

    @commands.command(name='Ticket')
    async def ticket(self, ctx):
        await ctx.send("https://discord.com/channels/1182380144887865406/1182380148436242475")

    @commands.command(name='Support')
    async def support(self, ctx):
        await ctx.send("https://discord.com/channels/1182380144887865406/1182380148436242476")

    @commands.command(name='list_members')
    async def list_members(self, ctx, role_input):
        # Get role based on the provided role_input (case-insensitive)
        role = discord.utils.get(ctx.guild.roles, name=role_input, case_insensitive=True) or discord.utils.get(ctx.guild.roles, mention=role_input)

        if role:
            # Print some debug information
            print(f"Role found: {role.name}, {role.id}")

            # Get all members with the specified role (case-insensitive comparison)
            members_with_role = [member.display_name for member in role.members]

            if members_with_role:
                await ctx.send(f"Members with the role {role.mention}: {', '.join(members_with_role)}")
            else:
                await ctx.send(f"No members found with the role {role.mention}.")
        else:
            await ctx.send(f"Role {role_input} not found.")

# Add the custom commands cog
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')
    await bot.add_cog(CustomCommands(bot))

# Simple command
@bot.command(name='hello')
async def hello(ctx):
    await ctx.send('Hello!')

Token = os.environ.get("TOKEN")

# Run the bot with the token
bot.run(Token)





















