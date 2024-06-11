import discord
from utils import discord_helpers


async def show_role_members(
    interaction: discord.Interaction,
    discord_role_1: discord.Role,
    discord_role_2: discord.Role = None,
):
    try:
        await interaction.response.defer()
        #######################################################################
        #                               RECORDS                               #
        #######################################################################
        #######################################################################
        #                             PROCESSING                              #
        #######################################################################
        # Guild
        guild = interaction.guild
        assert guild, "Error: Guild not found."
        all_members: list[discord.Member] = guild.members
        # Role 1
        assert discord_role_1, "Error: Role not found."
        members_with_roles = [
            member for member in all_members if discord_role_1 in member.roles
        ]
        # Role 2
        if discord_role_2:
            members_with_roles = [
                member
                for member in members_with_roles
                if discord_role_2 in member.roles
            ]
        # Sort
        members_with_roles.sort(key=lambda member: member.display_name)
        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        response_list = [member.mention for member in members_with_roles]
        response_message = (
            f"Members with {discord_role_1.mention} {'and ' + discord_role_2.mention  + ' roles' if discord_role_2 else 'role'} (limited to 2000 chars): [{', '.join(response_list)}]",
        )
        await discord_helpers.final_message(
            interaction=interaction,
            message=response_message[:2000],
            ephemeral=True,
        )
        #######################################################################
        #                               LOGGING                               #
        #######################################################################

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message, ephemeral=True)
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
