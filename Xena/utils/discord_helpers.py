import discord


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


### Formatting ###


async def code_block(text: str, language: str = "") -> str:
    """Format text as a code block"""
    return f"```{language}\n{text}```"
