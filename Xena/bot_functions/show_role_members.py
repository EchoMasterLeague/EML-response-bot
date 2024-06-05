import discord


async def show_role_members(
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
