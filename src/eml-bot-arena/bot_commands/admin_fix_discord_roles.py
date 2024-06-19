from database.database_full import FullDatabase
from database.fields import SuspensionFields, TeamFields, TeamPlayerFields, PlayerFields
from utils import discord_helpers, general_helpers
import datetime
import discord
import constants
from utils import discord_helpers, general_helpers
import json
import bot_helpers
import logging

logger = logging.getLogger(__name__)


async def admin_fix_discord_roles(
    database: FullDatabase, interaction: discord.Interaction
):
    """Correct any Discord Role issues"""
    try:
        await interaction.response.defer(ephemeral=True)
        debug = False
        #######################################################################
        #                               RECORDS                               #
        #######################################################################
        # Player
        player_records = await database.table_player.get_player_records()
        # Team
        team_records = await database.table_team.get_team_records()
        # TeamPlayer
        team_player_records = await database.table_team_player.get_team_player_records()
        # Suspension
        suspensions = await database.table_suspension.get_suspension_records()
        # CoolDown
        cooldowns = await database.table_cooldown.get_cooldown_records()

        #######################################################################
        #                             PROCESSING                              #
        #######################################################################
        logs = ""
        # Role Prefixes
        role_prefixes = [
            constants.DISCORD_ROLE_PREFIX_TEAM,
            constants.DISCORD_ROLE_PREFIX_PLAYER,
            constants.DISCORD_ROLE_PREFIX_CAPTAIN,
            constants.DISCORD_ROLE_PREFIX_CO_CAPTAIN,
            constants.DISCORD_ROLE_LEAGUE_SUB,
        ]
        database_players_by_role = {}
        discord_players_by_role = {}
        # Lookups
        lookup_team_name_by_id = {}
        lookup_player_discord_id_by_id = {}
        lookup_player_region_by_id = {}
        # Walk Discord Members
        for member in interaction.guild.members:
            for role in member.roles:
                role_name = role.name
                if any(role_name.startswith(prefix) for prefix in role_prefixes):
                    if not discord_players_by_role.get(role_name):
                        discord_players_by_role[role_name] = []
                    discord_players_by_role[role_name] += [str(member.id)]
        # Walk Teams
        for team_record in team_records:
            team_id = await team_record.get_field(TeamFields.record_id)
            team_name = await team_record.get_field(TeamFields.team_name)
            lookup_team_name_by_id[team_id] = team_name
        # Walk Players
        for player_record in player_records:
            player_id = await player_record.get_field(PlayerFields.record_id)
            discord_id = await player_record.get_field(PlayerFields.discord_id)
            region = await player_record.get_field(PlayerFields.region)
            is_sub = await player_record.get_field(PlayerFields.is_sub)
            # Lookups
            lookup_player_discord_id_by_id[player_id] = discord_id
            lookup_player_region_by_id[player_id] = region
            # Player<REGION>
            role_name = f"{constants.DISCORD_ROLE_PREFIX_PLAYER}{region}"
            if not database_players_by_role.get(role_name):
                database_players_by_role[role_name] = []
            database_players_by_role[role_name] += [str(discord_id)]
            # League Sub
            if is_sub:
                role_name = f"{constants.DISCORD_ROLE_LEAGUE_SUB}"
                if not database_players_by_role.get(role_name):
                    database_players_by_role[role_name] = []
                database_players_by_role[role_name] += [str(discord_id)]
        # Walk TeamPlayers
        for team_player_record in team_player_records:
            team_id = await team_player_record.get_field(TeamPlayerFields.team_id)
            player_id = await team_player_record.get_field(TeamPlayerFields.player_id)
            is_captain = await team_player_record.get_field(TeamPlayerFields.is_captain)
            is_co_captain = await team_player_record.get_field(
                TeamPlayerFields.is_co_captain
            )
            discord_id = lookup_player_discord_id_by_id.get(player_id)
            region = lookup_player_region_by_id.get(player_id)
            team_name = lookup_team_name_by_id.get(team_id)
            # Team
            role_name = f"{constants.DISCORD_ROLE_PREFIX_TEAM}{team_name}"
            if not database_players_by_role.get(role_name):
                database_players_by_role[role_name] = []
            database_players_by_role[role_name] += [str(discord_id)]
            # Captain<REGION>
            if is_captain:
                role_name = f"{constants.DISCORD_ROLE_PREFIX_CAPTAIN}{region}"
                if not database_players_by_role.get(role_name):
                    database_players_by_role[role_name] = []
                database_players_by_role[role_name] += [str(discord_id)]
            # CoCaptain<REGION>
            if is_co_captain:
                role_name = f"{constants.DISCORD_ROLE_PREFIX_CO_CAPTAIN}{region}"
                if not database_players_by_role.get(role_name):
                    database_players_by_role[role_name] = []
                database_players_by_role[role_name] += [str(discord_id)]
        # Sort Lists
        for role_name, discord_ids in discord_players_by_role.items():
            discord_players_by_role[role_name] = sorted(discord_ids)
        discord_players_by_role = dict(sorted(discord_players_by_role.items()))
        if debug:
            logs += "\n".join(
                [
                    "###############################################################################",
                    "All League Players by Role from Discord",
                    json.dumps(discord_players_by_role, indent=4),
                    "###############################################################################",
                    "",
                ]
            )

        for role_name, discord_ids in database_players_by_role.items():
            database_players_by_role[role_name] = sorted(discord_ids)
        database_players_by_role = dict(sorted(database_players_by_role.items()))
        if debug:
            logs += "\n".join(
                [
                    "###############################################################################",
                    "All League Players by Role from Database",
                    json.dumps(database_players_by_role, indent=4),
                    "###############################################################################",
                    "",
                ]
            )

        # Remove empty roles
        count_empty = 0
        other_roles = []
        player_roles = []
        empty_other_roles = []
        empty_player_roles = []
        # get guild roles
        logs += "\n".join(
            [
                "Player Role Prefixes:",
                json.dumps(role_prefixes, indent=4),
                "",
            ]
        )
        for role in interaction.guild.roles:
            player_role = False
            if any(role.name.startswith(prefix) for prefix in role_prefixes):
                player_role = True
            if player_role:
                player_roles += [role.name]
            else:
                other_roles += [role.name]
            if not role.members:
                if player_role:
                    empty_player_roles += [role.name]
                else:
                    empty_other_roles += [role.name]

        # sort roles
        other_roles = sorted(other_roles)
        player_roles = sorted(player_roles)
        empty_other_roles = sorted(empty_other_roles)
        empty_player_roles = sorted(empty_player_roles)
        # show roles
        all_guild_roles = {
            "All Player Roles": player_roles,
            "All Other Roles": other_roles,
        }
        empty_guild_roles = {
            "Empty Player Roles": empty_player_roles,
            "Empty Other Roles": empty_other_roles,
        }
        logs += "\n".join(
            [
                "All Guild Roles:",
                json.dumps(all_guild_roles, indent=4),
                "",
            ]
        )
        logs += "\n".join(
            [
                "Empty Guild Roles:",
                json.dumps(empty_guild_roles, indent=4),
                "",
            ]
        )
        # remove empty roles
        for role_name in empty_player_roles:
            # WARNING
            # await discord_helpers.guild_role_remove_if_exists(interaction.guild, role_name)
            count_empty += 1
            # logger.warn(f"  DISCORD: Empty Guild Role of type `{role_type}` was `{removed}` -- `{role_name}`")

        # Players with roles in discord, but not in the database
        discord_players_without_db = {}
        for role_name, discord_ids in discord_players_by_role.items():
            for discord_id in discord_ids:
                is_in_other_list = False
                for discord_id_2 in database_players_by_role.get(role_name, []):
                    if discord_id == discord_id_2:
                        is_in_other_list = True
                if not is_in_other_list:
                    if not discord_players_without_db.get(role_name):
                        discord_players_without_db[role_name] = []
                    discord_players_without_db[role_name] += [discord_id]
        discord_players_without_db = dict(sorted(discord_players_without_db.items()))
        # Remove roles from players without a record
        count_removed = 0
        player_role_removals = {}
        for role_name, discord_ids in discord_players_without_db.items():
            for discord_id in discord_ids:
                member = await discord_helpers.member_from_discord_id(
                    interaction.guild, discord_id
                )
                if not player_role_removals.get(role_name):
                    player_role_removals[role_name] = []
                player_role_removals[role_name] += [
                    f"{member.display_name}({member.id})"
                ]
                # WARNING
                # await discord_helpers.member_role_remove_by_prefix(member, role_name)
                count_removed += 1
        player_role_removals = dict(sorted(player_role_removals.items()))
        logs += "\n".join(
            [
                "###############################################################################",
                "(player roles in discord that do not match database records)",
                "Player Roles to REMOVE:",
                json.dumps(player_role_removals, indent=4),
                "",
            ]
        )

        # Players with roles in the database, but not in discord
        db_players_without_discord = {}
        for role_name, discord_ids in database_players_by_role.items():
            for discord_id in discord_ids:
                is_in_other_list = False
                for discord_id_2 in discord_players_by_role.get(role_name, []):
                    if discord_id == discord_id_2:
                        is_in_other_list = True
                if not is_in_other_list:
                    if not db_players_without_discord.get(role_name):
                        db_players_without_discord[role_name] = []
                    db_players_without_discord[role_name] += [discord_id]
        db_players_without_discord = dict(sorted(db_players_without_discord.items()))
        # Add roles to players with a record
        count_added = 0
        player_role_additions = {}
        for role_name, discord_ids in db_players_without_discord.items():
            for discord_id in discord_ids:
                member = await discord_helpers.member_from_discord_id(
                    interaction.guild, discord_id
                )
                if not player_role_additions.get(role_name):
                    player_role_additions[role_name] = []
                player_role_additions[role_name] += [
                    f"{member.display_name}({member.id})"
                ]
                # WARNING
                # await discord_helpers.member_role_add_if_needed(member, role_name)
                count_added += 1
        player_role_additions = dict(sorted(player_role_additions.items()))
        logs += "\n".join(
            [
                "###############################################################################",
                "(player roles needed in discord to match database records)",
                "Player Roles to ADD:",
                json.dumps(player_role_additions, indent=4),
                "",
            ]
        )

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        response_dictionary = {
            "player_role_dels_needed": count_removed,
            "player_role_adds_needed": count_added,
            "empty_player_role_count": count_empty,
        }
        response_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(response_dictionary), "json"
        )
        await discord_helpers.final_message(
            interaction=interaction,
            message="\n".join(
                [
                    f"Player roles to be corrected:",
                    f"{response_code_block}",
                    "",
                ]
            ),
            files=[await discord_helpers.discord_file_from_string(logs, "output.txt")],
            ephemeral=True,
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################

    # Errors
    except AssertionError as message:
        await discord_helpers.fail_message(interaction, message, ephemeral=True)
    except Exception as error:
        await discord_helpers.error_message(interaction, error, ephemeral=True)
