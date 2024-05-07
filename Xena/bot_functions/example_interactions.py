import discord


class EampleInteractions:
    """Examples of Discord bot interactions"""

    async def example_interaction_simple(
        self,
        interaction: discord.Interaction,
    ):
        """Example of a simple interaction flow

        This is a common pattern when the bot needs to respond to the user only once in a single interaction.
        """
        # await interaction.response.defer()
        await interaction.response.send_message("Hello, World!")
        # await interaction.response.edit_message("Goodbye, cruel world...")
        # await interaction.followup.send("I'm outta here!")
        # await interaction.followup.edit_message("Just kidding, I'm back!")

    async def example_interaction_multiple_steps(
        self,
        interaction: discord.Interaction,
    ):
        """Example of a complete interaction flow

        This is a common pattern when the bot needs to respond to the user multiple times in a single interaction.
        Compare this function to the example_interaction_slow_initial_response function.
        The commented-out portions of these two function are incompatible with each other.
        """
        # await interaction.response.defer()
        await interaction.response.send_message("Hello, World!")
        await interaction.response.edit_message("Goodbye, cruel world...")
        await interaction.followup.send("I'm outta here!")
        await interaction.followup.edit_message("Just kidding, I'm back!")

    async def example_interaction_slow_initial_response(
        self,
        interaction: discord.Interaction,
    ):
        """Example of an interaction flow when the first response may take longer than 3 seconds to generate.

        This is a common pattern when the bot needs to perform a long-running task before it can respond to the user.
        The bot must respond within 3 seconds to avoid a timeout error. `defer()` serves as this initial response.
        Compare this function to the example_interaction_multiple_steps function.
        The commented-out portions of these two function are incompatible with each other.
        """

        await interaction.response.defer()
        # await interaction.response.send_message("Hello, World!")
        # await interaction.response.edit_message("Goodbye, cruel world...")
        await interaction.followup.send("I'm outta here!")
        await interaction.followup.edit_message("Just kidding, I'm back!")
