import discord
import json
import logging

logger = logging.getLogger(__name__)


async def command_log(args: dict = {}):
    """Log command usage to console"""
    try:
        # Variables
        interaction: discord.Interaction = args.pop("interaction")
        command_dict = {
            # "User": f"{interaction.user.display_name}({interaction.user.id})",
            "command": f"/{interaction.command.name}",
            "args": args,
        }
        # Message
        logger.info(
            "\n".join(
                [
                    f"Command Execution by: {interaction.user.display_name}({interaction.user.id})",
                    f"{json.dumps(command_dict,indent=4)}",
                ]
            )
        )
    except Exception as error:
        logger.exception(error)
