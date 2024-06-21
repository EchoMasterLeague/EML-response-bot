import discord
import constants
from io import BytesIO
from utils import general_helpers
import json
import logging

logger = logging.getLogger(__name__)


### Formatting ###


async def code_block(text: str, language: str = "json") -> str:
    """Format text as a code block"""
    return f"```{language}\n{text}```"


### Messages ###


async def final_message(
    interaction: discord.Interaction,
    message: str,
    ephemeral: bool = False,
    files: list[discord.File] = [],
    failure: bool = False,
):
    """Send a final message to an interaction"""
    message_file = None
    if len(str(message)) > constants.DISCORD_MESSAGE_SIZE_LIMIT:
        # create a temporary file to hold the message
        data_buffer = BytesIO(message.encode("utf-8"))
        message_file = discord.File(fp=data_buffer, filename="message.txt")
        message = "Message too long. See attached file."
    if message_file:
        files = [message_file] + files
    if not interaction.response.is_done():
        await interaction.response.send_message(
            content=message, ephemeral=ephemeral, files=files
        )
    else:
        await interaction.followup.send(
            content=message, ephemeral=ephemeral, files=files
        )
    # Log result
    command = f"/{interaction.command.name}"
    command_dict = {
        "command": command,
        "success": not failure,
        "message": str(message),
    }
    if files:
        command_dict["files"] = len(files)
    logger.info(
        "\n".join(
            [
                f"Command Result for: {interaction.user.display_name}({interaction.user.id})",
                f"{json.dumps(command_dict, indent=4)}",
            ]
        )
    )
    await log_to_debug_channel(
        interaction=interaction,
        command=command,
        response=message,
        success=not failure,
        files=files,
    )


async def fail_message(
    interaction: discord.Interaction,
    message: str,
    ephemeral: bool = False,
):
    """Send an error message to an interaction, and raise the error."""
    await final_message(
        interaction=interaction, message=message, ephemeral=ephemeral, failure=True
    )


async def error_message(
    interaction: discord.Interaction,
    error: Exception,
    message: str = "Error: Something went wrong.",
    ephemeral: bool = False,
):
    """Send an error message to an interaction, and raise the error."""
    await final_message(
        interaction=interaction, message=message, ephemeral=ephemeral, failure=True
    )
    raise error


async def log_to_channel(
    channel: discord.TextChannel = None,
    channel_name: str = None,
    interaction: discord.Interaction = None,
    message: str = None,
    embed: discord.Embed = None,
):
    """Send a log message to a channel"""
    if not channel and not interaction:
        return False
    if interaction:
        if not channel_name:
            channel_name = constants.DISCORD_CHANNEL_BOT_LOGS
        channel = await get_guild_channel(
            interaction=interaction, channel_name=channel_name
        )
    await channel.send(content=message, embed=embed)


async def log_to_debug_channel(
    interaction: discord.Interaction,
    request: str = None,
    response: str = None,
    files: list[discord.File] = [],
    success: bool = True,
    command: str = None,
    command_args: dict[str, any] = {},
):
    """Send a log message to the debugging channel"""
    debug_channel = await get_guild_channel(
        interaction=interaction, channel_name=constants.DISCORD_CHANNEL_BOT_DEBUG_LOGS
    )

    if request:
        color = discord.Color.blue()
        command_args_block = await code_block(
            await general_helpers.format_json(command_args)
        )
        debug_embed = discord.Embed(description=f"{request}", color=color)
        debug_embed.add_field(name="Command", value=command)
        debug_embed.add_field(name="Args", value=command_args_block, inline=False)
        await debug_channel.send(embed=debug_embed, files=files)
    if response:
        color = discord.Color.green()
        if not success:
            color = discord.Color.red()
        heading = f"Command Result for: {interaction.user.display_name}({interaction.user.id})"
        debug_embed = discord.Embed(description=f"{heading}", color=color)
        debug_embed.add_field(name="Success", value=success)
        debug_embed.add_field(name="Command", value=command)
        debug_embed.add_field(name="Response", value=response, inline=False)
        await debug_channel.send(embed=debug_embed, files=files)


### Files ###


async def discord_file_from_string(
    content: str, filename: str = "file.txt"
) -> discord.File:
    """Convert a string to a Discord file"""
    data_buffer = BytesIO(content.encode("utf-8"))
    return discord.File(fp=data_buffer, filename=filename)


### Channels ###


async def get_guild_channel(
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
        raise ValueError("Channel name required")
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


async def member_is_admin(member: discord.Member):
    """Check if a Guild Member is an admin"""
    admin_roles = constants.DISCORD_ROLES_LIST_ADMIN.split(",")
    admin_roles = [role.strip() for role in admin_roles]
    member_roles = [role.name for role in member.roles]
    common_roles = set(admin_roles).intersection(member_roles)
    if common_roles:
        return True
    return False


### Players ###


async def member_add_player_role(member: discord.Member, region: str):
    """Add a Player role to a Guild Member"""
    role_name = f"{constants.DISCORD_ROLE_PREFIX_PLAYER}{region}"
    role = await guild_role_get_or_create(member.guild, role_name)
    await member.add_roles(role)
    return True


async def member_remove_player_role(member: discord.Member):
    """Remove a Player role from a Guild Member"""
    prefixes = [constants.DISCORD_ROLE_PREFIX_PLAYER]
    for role in member.roles:
        if any(role.name.startswith(prefix) for prefix in prefixes):
            await member.remove_roles(role)
    return True


async def member_add_league_sub_role(member: discord.Member):
    """Add the League Substitute role to a Guild Member"""
    role = await guild_role_get_or_create(
        guild=member.guild, role_name=constants.DISCORD_ROLE_LEAGUE_SUB
    )
    await member.add_roles(role)
    return True


async def member_remove_league_sub_role(member: discord.Member):
    """Remove the League Substitute role from a Guild Member"""
    for role in member.roles:
        if role.name == constants.DISCORD_ROLE_LEAGUE_SUB:
            await member.remove_roles(role)
    return True


async def member_remove_all_league_roles(member: discord.Member):
    """Remove all League roles from a Guild Member"""
    await member_remove_team_roles(member)
    await member_remove_league_sub_role(member)
    await member_remove_player_role(member)
    return True


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
        role_name = f"{constants.DISCORD_ROLE_PREFIX_TEAM}{team_name}"
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


### Roles for Teams ###


async def member_add_team_role(member: discord.Member, team_name: str):
    """Add a Team role to a Guild Member"""
    role_name = f"{constants.DISCORD_ROLE_PREFIX_TEAM}{team_name}"
    role = await guild_role_get_or_create(member.guild, role_name)
    await member.add_roles(role)
    return True


async def member_remove_team_roles(member: discord.Member):
    """Remove all Team roles from a Guild Member"""
    prefixes = [
        constants.DISCORD_ROLE_PREFIX_TEAM,
        constants.DISCORD_ROLE_PREFIX_CAPTAIN,
        constants.DISCORD_ROLE_PREFIX_CO_CAPTAIN,
    ]
    for role in member.roles:
        if any(role.name.startswith(prefix) for prefix in prefixes):
            await member.remove_roles(role)
    return True


async def guild_remove_team_role(guild: discord.Guild, team_name: str):
    """Remove a Team role from a Guild"""
    role_name = f"{constants.DISCORD_ROLE_PREFIX_TEAM}{team_name}"
    return await guild_role_remove_if_exists(guild, role_name)


async def member_add_captain_role(member: discord.Member, region: str):
    """Add a Captain role to a Guild Member"""
    role_name = f"{constants.DISCORD_ROLE_PREFIX_CAPTAIN}{region}"
    role = await guild_role_get_or_create(member.guild, role_name)
    await member.add_roles(role)
    return True


async def member_remove_captain_roles(member: discord.Member):
    """Remove a Captain role from a Guild Member"""
    prefixes = [
        constants.DISCORD_ROLE_PREFIX_CAPTAIN,
        constants.DISCORD_ROLE_PREFIX_CO_CAPTAIN,
    ]
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


async def get_team_name_from_role(team_role: discord.Role):
    """Get the Team name from a role name"""
    return team_role.name.replace(constants.DISCORD_ROLE_PREFIX_TEAM, "")
