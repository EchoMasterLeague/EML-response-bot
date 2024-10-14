from database.database_full import FullDatabase
from database.fields import ConstantsFields
from utils import discord_helpers
import constants
import discord
import logging

logger = logging.getLogger(__name__)


async def get_constant(
    database: FullDatabase,
    interaction: discord.Interaction,
    constant_name: str,
    default_str: str,
    skip_db: bool = False,
):
    try:
        record = None
        retStr = default_str

        if not skip_db:
            constrecs = (
                await database.table_constants.get_constants_records(
                    constant_name)
                )
            record = constrecs[0] if constrecs else None

        if record:
            retStr = await record.get_field(ConstantsFields.value)

        return retStr
    # Errors
    except Exception as error:
        await discord_helpers.error_message(interaction, error)
    return False
