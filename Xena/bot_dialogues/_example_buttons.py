import discord
import discord.ext.commands as commands


############################
### Button Class Example ###
############################
class ButtonExample(discord.ui.View):
    """This class is an example of a set of buttons for an interactive bot message.

    You probably do not need all of the possible buttons all of the time, but they are here for reference.
    Reference: https://gist.github.com/lykn/bac99b06d45ff8eed34c2220d86b6bf4

    Note: The callback functions can only reference objects within their button class or passed into them.
    This limitation is important when deciding what to pass into the init function of your button class.
    """

    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Button Text", style=discord.ButtonStyle.primary)
    async def primary_button_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        button.disabled = True
        ### Code to be run for this button goes here
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Secondary Button", style=discord.ButtonStyle.secondary)
    async def secondary_button_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        button.disabled = True
        ### Code to be run for this button goes here
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Success Button", style=discord.ButtonStyle.success)
    async def success_button_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        button.disabled = True
        ### Code to be run for this button goes here
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Danger Button", style=discord.ButtonStyle.danger)
    async def danger_button_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        button.disabled = True
        ### Code to be run for this button goes here
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Change All", style=discord.ButtonStyle.success)
    async def color_changing_button_callback(
        self, interaction: discord.Interaction, child: discord.ui.Button
    ):
        for child in self.children:
            """This loop disables all buttons in this dialogue/view."""
            child.disabled = True
        ### Code to be run for this button goes here
        await interaction.response.edit_message(
            "All buttons have been disabled (and the orignial message replaced with this one).",
            view=self,
        )


############################
### Button Usage Example ###
############################
class ButtonExampleUsage:
    """This class exists to keep its code out of the global namespace. It should not be used.

    It is a valid class to keep syntax highlighting and ensure continued accuracy through breaking changes.
    If not for these puropses, this would just be a large comment block with the examples.
    """

    bot = commands.Bot(command_prefix=".")

    def __init__(self):
        raise NotImplementedError("ERROR: ButtonExampleUsage() is for reference only.")

    ### Reference Functions ###

    # Button Example
    @bot.tree.command(name="button_example_command")
    async def button_example_command(interaction: discord.Interaction):
        await interaction.response.send_message(
            "This message has buttons!", view=ButtonExample(), ephemeral=True
        )

    # URL Button Example
    @bot.tree.command(name="button_example_command_with_url_link")
    async def button_example_with_url_link(interaction: discord.Interaction):
        link_button = ButtonExample()
        link_button.add_item(
            discord.ui.Button(
                label="ClickMe!",
                style=discord.ButtonStyle.link,
                url="https://example.com/",
            )
        )
        await interaction.response.send_message(
            "This message has buttons!", view=link_button, ephemeral=True
        )
