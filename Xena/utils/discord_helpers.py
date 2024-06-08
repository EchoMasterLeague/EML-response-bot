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
    channel: discord.TextChannel = None,
    interaction: discord.Interaction = None,
    message: str = None,
):
    """Send a log message to a channel"""
    if not channel and not interaction:
        return False
    if interaction:
        channel = await get_log_channel(interaction=interaction)
    return await channel.send(content=message)


### Channels ###


async def get_log_channel(
    guild: discord.Guild = None,
    interaction: discord.Interaction = None,
    channel_name: str = None,
):
    """Get log channel"""
    if not guild and not interaction:
        raise ValueError("Guild or Interaction required")
    if interaction:
        guild = interaction.guild
    if not channel_name:
        channel_name = constants.GUILD_CHANNEL_BOT_LOGS
    return discord.utils.get(guild.channels, name=channel_name)


### Members ###


async def member_from_discord_id(guild: discord.Guild, discord_id: str):
    """Get a Guild Member from a Discord ID"""
    try:
        member = guild.get_member(discord_id)
        member = await guild.fetch_member(discord_id) if not member else member
        return member
    except discord.errors.NotFound:
        return None


### Roles ###


async def guild_role_get(guild: discord.Guild, role_name: str) -> discord.Role:
    """Get a role from a Discord server"""
    try:
        existing_role = discord.utils.get(guild.roles, name=role_name)
        return existing_role
    except discord.errors.NotFound:
        return None


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


async def role_mention(
    guild: discord.Guild,
    discord_id: str = None,
    role_name: str = None,
    team_name: str = None,
    player_name: str = None,
):
    if team_name:
        role_name = f"{constants.ROLE_PREFIX_TEAM}{team_name}"
    if role_name:
        role = await guild_role_get(guild, role_name)
        if role:
            return role.mention
        else:
            return f"`{role_name}`"
    if discord_id:
        member = await member_from_discord_id(guild, discord_id)
        if member:
            return member.mention
        return f"`({discord_id})`"
    if player_name:
        return f"`{player_name}`"
    return f"`(unknown)`"


async def role_mention_player(guild: discord.Guild, player_id: str):
    member = await member_from_discord_id(guild, player_id)
    return member.mention if member else f"`{player_id}`"


### Roles for Teams ###


async def get_team_role(guild: discord.Guild, team_name: str):
    """Get a Team role from a Guild"""
    try:
        role_name = f"{constants.ROLE_PREFIX_TEAM}{team_name}"
        role = await guild_role_get(guild, role_name)
        return role
    except discord.errors.NotFound:
        return None


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
