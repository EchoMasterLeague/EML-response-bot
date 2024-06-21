import discord
import json
from utils import discord_helpers, general_helpers
import logging

logger = logging.getLogger(__name__)


async def command_log(args: dict = {}):
    """Log command usage to console"""
    try:
        # Variables
        interaction: discord.Interaction = args.pop("interaction")
        command = f"/{interaction.command.name}"
        command_dict = {
            # "User": f"{interaction.user.display_name}({interaction.user.id})",
            "command": command,
            "args": args,
        }
        # Message
        heading = f"Command Execution by: {interaction.user.display_name}({interaction.user.id})"
        logger.info(
            "\n".join(
                [
                    heading,
                    f"{json.dumps(command_dict, indent=4)}",
                ]
            )
        )
        # Log
        await discord_helpers.log_to_debug_channel(
            interaction=interaction, request=heading, command=command, command_args=args
        )
    except Exception as error:
        logger.exception(error)
