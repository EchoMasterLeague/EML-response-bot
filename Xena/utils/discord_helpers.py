import discord
import constants


### Formatting ###


async def code_block(text: str, language: str = "json") -> str:
    """Format text as a code block"""
    return f"```{language}\n{text}```"


### Messages ###


async def final_message(interaction: discord.Interaction, message: str):
    """Send a final message to an interaction"""
    if not interaction.response.is_done():
        return await interaction.response.send_message(message)
    else:
        return await interaction.followup.send(message)


async def error_message(
    interaction: discord.Interaction,
    error: Exception,
    message: str = "Error: Something went wrong.",
):
    """Send an error message to an interaction, and raise the error."""
    await final_message(interaction, message)
    raise error


async def log_to_channel(
    channel: discord.TextChannel,
    message: str = None,
    dictionary: dict = None,
    embed: discord.Embed = None,
):
    """Send a log message to a channel"""
    if not channel:
        return False
    embed = discord.Embed(description=message) if message else embed
    embed = discord.Embed.from_dict(dictionary) if dictionary else embed
    if embed:
        embed.color = discord.Color.green() if not embed.color else embed.color
        return await channel.send(embed=embed)
    return False


### Channels ###


async def get_channel(client: discord.Client, channel_id: int):
    """Get a channel by ID"""
    channel = client.get_channel(channel_id)
    channel = await client.fetch_channel(channel_id) if not channel else channel
    return channel


### Members ###


async def member_from_discord_id(guild: discord.Guild, discord_id: str):
    """Get a Guild Member from a Discord ID"""
    member = guild.get_member(discord_id)
    member = await guild.fetch_member(discord_id) if not member else member
    return member


### Roles ###


async def guild_role_get_or_create(
    guild: discord.Guild, role_name: str
) -> discord.Role:
    """Ensure a role exists in the Discord server"""
    existing_role = discord.utils.get(guild.roles, name=role_name)
    if existing_role:
        return existing_role
    return await guild.create_role(name=role_name)


async def guild_role_remove_if_exists(guild: discord.Guild, role_name: str) -> bool:
    """Remove a role from the Discord server if it exists"""
    existing_role = discord.utils.get(guild.roles, name=role_name)
    if existing_role:
        await existing_role.delete()
    return True


async def member_role_add_if_needed(member: discord.Member, role_name: str) -> bool:
    """Add a role to a member if it does not already exist"""
    role = discord.utils.get(member.roles, name=role_name)
    if not role:
        role = await guild_role_get_or_create(member.guild, role_name)
    await member.add_roles(role)
    return True


async def member_role_remove_by_prefix(
    member: discord.Member, role_prefix: str
) -> bool:
    """Remove all roles from a member that match a prefix"""
    for role in member.roles:
        if role.name.startswith(role_prefix):
            await member.remove_roles(role)
    return True


### Roles for Teams ###


async def get_team_role(guild: discord.Guild, team_name: str):
    """Get a Team role from a Guild"""
    role_name = f"{constants.ROLE_PREFIX_TEAM}{team_name}"
    return discord.utils.get(guild.roles, name=role_name)


async def member_add_team_role(member: discord.Member, team_name: str):
    """Add a Team role to a Guild Member"""
    role_name = f"{constants.ROLE_PREFIX_TEAM}{team_name}"
    role = await guild_role_get_or_create(member.guild, role_name)
    await member.add_roles(role)
    return True


async def member_remove_team_roles(member: discord.Member):
    """Remove all Team roles from a Guild Member"""
    prefixes = [
        constants.ROLE_PREFIX_TEAM,
        constants.ROLE_PREFIX_CAPTAIN,
        constants.ROLE_PREFIX_CO_CAPTAIN,
    ]
    for role in member.roles:
        if any(role.name.startswith(prefix) for prefix in prefixes):
            await member.remove_roles(role)
    return True


async def guild_remove_team_role(guild: discord.Guild, team_name: str):
    """Remove a Team role from a Guild"""
    role_name = f"{constants.ROLE_PREFIX_TEAM}{team_name}"
    return await guild_role_remove_if_exists(guild, role_name)


async def member_add_captain_role(member: discord.Member, region: str):
    """Add a Captain role to a Guild Member"""
    role_name = f"{constants.ROLE_PREFIX_CAPTAIN}{region}"
    role = await guild_role_get_or_create(member.guild, role_name)
    await member.add_roles(role)
    return True


async def member_add_co_captain_role(member: discord.Member, region: str):
    """Add a Captain role to a Guild Member"""
    role_name = f"{constants.ROLE_PREFIX_CO_CAPTAIN}{region}"
    role = await guild_role_get_or_create(member.guild, role_name)
    await member.add_roles(role)
    return True


async def member_remove_captain_roles(member: discord.Member):
    """Remove a Captain role from a Guild Member"""
    prefixes = [constants.ROLE_PREFIX_CAPTAIN, constants.ROLE_PREFIX_CO_CAPTAIN]
    for role in member.roles:
        if any(role.name.startswith(prefix) for prefix in prefixes):
            await member.remove_roles(role)
    return True


async def add_member_to_team(member: discord.Member, team_name: str):
    """Add a Discord Member to a Team

    Note: This only handles the Discord roles. Database changes are not handled."""
    await member_remove_team_roles(member)
    await member_add_team_role(member, team_name)
    return True
