from utils import general_helpers
import discord


async def command_log(args: dict = {}):
    """Log command usage"""
    try:
        # Log
        timstamp = await general_helpers.iso_timestamp()
        interaction: discord.Interaction = args.pop("interaction")
        user = f"{interaction.user.display_name}({interaction.user.id})"
        command_name = interaction.command.name
        print(f"{timstamp}: /{command_name} {args} -- {user}")
    except Exception as error:
        print(error)
