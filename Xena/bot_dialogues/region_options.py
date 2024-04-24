import discord
import discord.ext.commands as commands


class ButtonRegionOptions(discord.ui.View):
    """Options to choose a region when registering a player"""

    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)
        self.value = None

    async def disable_buttons(self):
        for child in self.children:
            """This loop disables all buttons in this dialogue/view."""
            if type(child) == discord.ui.Button:
                child.disabled = True

    async def select(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.style = discord.ButtonStyle.success
        await self.disable_buttons()
        self.stop()

    @discord.ui.button(label="Europe", style=discord.ButtonStyle.secondary)
    async def success_button_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.value = "Europe"
        await self.select(interaction, button)

    @discord.ui.button(label="North America", style=discord.ButtonStyle.secondary)
    async def secondary_button_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.value = "North America"
        await self.select(interaction, button)

    @discord.ui.button(label="Oceania", style=discord.ButtonStyle.secondary)
    async def primary_button_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.value = "Oceania"
        await self.select(interaction, button)
