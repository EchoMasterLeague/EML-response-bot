import discord
from utils import discord_helpers


async def show_role_members(
    interaction: discord.Interaction,
    role_input1: str,
    role_input2: str = None,
):
    try:
        #######################################################################
        #                               RECORDS                               #
        #######################################################################
        #######################################################################
        #                             PROCESSING                              #
        #######################################################################
        # Get the guild from the interaction
        guild = interaction.guild

        if guild:
            all_roles: list[discord.Role] = await guild.fetch_roles()
            all_members: list[discord.Member] = guild.members
            # Get role based on the provided role_input1 (case-insensitive)
            role1_matches = [
                role
                for role in all_roles
                if role_input1.casefold() == role.name.casefold()
            ]
            role1 = role1_matches[0] if role1_matches else None
            # If role_input2 is provided, get the role based on it (case-insensitive)
            role2 = None
            if role_input2:
                role2_matches = [
                    role
                    for role in all_roles
                    if role_input2.casefold() == role.name.casefold()
                ]
                role2 = role2_matches[0] if role2_matches else None
            if role1:
                # Get members with specified roles (case-insensitive comparison)
                members_with_roles = [
                    member for member in all_members if role1 in member.roles
                ]
                if role2:
                    members_with_roles = [
                        member for member in members_with_roles if role2 in member.roles
                    ]
                if members_with_roles:
                    member_mentions = [member.mention for member in members_with_roles]
                    await interaction.response.send_message(
                        f"Members with {role1.mention} role{' and ' + role2.mention if role2 else ''}: {', '.join(member_mentions)}",
                        ephemeral=True,
                    )
                else:
                    await interaction.response.send_message(
                        f"No members found with {role1.mention} role{' and ' + role2.mention if role2 else ''}.",
                        ephemeral=True,
                    )
            else:
                await interaction.response.send_message(
                    "Role not found.", ephemeral=True
                )
        else:
            await interaction.response.send_message(
                "Error: Guild not found.", ephemeral=True
            )

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        #######################################################################
        #                               LOGGING                               #
        #######################################################################

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
