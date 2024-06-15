from database.database_full import FullDatabase
from database.fields import SuspensionFields, TeamFields, TeamPlayerFields, PlayerFields
from utils import discord_helpers, general_helpers
import datetime
import discord
import constants
from utils import discord_helpers, general_helpers


async def admin_fix_discord_roles(
    database: FullDatabase, interaction: discord.Interaction
):
    """Correct any Discord Role issues"""
    try:
        await interaction.response.defer(ephemeral=True)
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
        logs = []
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
                    discord_players_by_role[role_name] += [member.id]
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
            database_players_by_role[role_name] += [discord_id]
            # League Sub
            if is_sub:
                role_name = f"{constants.DISCORD_ROLE_LEAGUE_SUB}"
                if not database_players_by_role.get(role_name):
                    database_players_by_role[role_name] = []
                database_players_by_role[role_name] += [discord_id]
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
            database_players_by_role[role_name] += [discord_id]
            # Captain<REGION>
            if is_captain:
                role_name = f"{constants.DISCORD_ROLE_PREFIX_CAPTAIN}{region}"
                if not database_players_by_role.get(role_name):
                    database_players_by_role[role_name] = []
                database_players_by_role[role_name] += [discord_id]
            # CoCaptain<REGION>
            if is_co_captain:
                role_name = f"{constants.DISCORD_ROLE_PREFIX_CO_CAPTAIN}{region}"
                if not database_players_by_role.get(role_name):
                    database_players_by_role[role_name] = []
                database_players_by_role[role_name] += [discord_id]
        # Players with roles in discord, but not in the database
        discord_players_without_db = {}
        for role_name, discord_ids in discord_players_by_role.items():
            for discord_id in discord_ids:
                if discord_id not in database_players_by_role.get(role_name, []):
                    if not discord_players_without_db.get(role_name):
                        discord_players_without_db[role_name] = []
                    discord_players_without_db[role_name] += [discord_id]
        # Players with roles in the database, but not in discord
        database_players_without_discord = {}
        for role_name, discord_ids in database_players_by_role.items():
            for discord_id in discord_ids:
                if discord_id not in discord_players_by_role.get(role_name, []):
                    if not database_players_without_discord.get(role_name):
                        database_players_without_discord[role_name] = []
                    database_players_without_discord[role_name] += [discord_id]
        # Remove roles from players without a record
        count_removed = 0
        for role_name, discord_ids in discord_players_without_db.items():
            for discord_id in discord_ids:
                member = await discord_helpers.member_from_discord_id(
                    interaction.guild, discord_id
                )
                role = await discord_helpers.guild_role_get(
                    interaction.guild, role_name
                )
                # await member.remove_roles(role)
                logs += [
                    f"  DISCORD: Member Removed from `{role_name}` -- {member.display_name}({member.id})"
                ]
                count_removed += 1
        # Add roles to players with a record
        count_added = 0
        for role_name, discord_ids in database_players_without_discord.items():
            for discord_id in discord_ids:
                member = await discord_helpers.member_from_discord_id(
                    interaction.guild, discord_id
                )
                role = await discord_helpers.guild_role_get(
                    interaction.guild, role_name
                )
                # await member.add_roles(role)
                logs += [
                    f"  DISCORD: Member Added to `{role_name}` -- {member.display_name}({member.id})"
                ]
                count_added += 1
        # Remove empty roles
        count_empty = 0
        for role in interaction.guild.roles:
            role_name = role.name
            player_role = False
            empty = False
            member_count = len(role.members)
            if any(role_name.startswith(prefix) for prefix in role_prefixes):
                player_role = True
            if not role.members:
                empty = True
                if player_role:
                    # await role.delete()
                    count_empty += 1
            role_type = "LEAGUE" if player_role else "SYSTEM"
            removed = "DELETED" if empty else "KEPT___"
            member_count = f"{member_count:3}"
            logs += [
                f"  DISCORD: {removed} {role_type} role with ({member_count}) members -- `{role_name}`"
            ]
        print("\n".join(sorted(logs)))

        #######################################################################
        #                              RESPONSE                               #
        #######################################################################
        response_dictionary = {
            "player_role_removals": count_removed,
            "player_role_additions": count_added,
            "empty_roles_removed": count_empty,
        }
        response_code_block = await discord_helpers.code_block(
            await general_helpers.format_json(response_dictionary), "json"
        )
        await discord_helpers.final_message(
            interaction=interaction,
            message="\n".join(
                [
                    f"Player roles corrected:",
                    f"{response_code_block}",
                ]
            ),
            ephemeral=True,
        )

        #######################################################################
        #                               LOGGING                               #
        #######################################################################

    # Errors
    except AssertionError as message:
        await discord_helpers.final_message(interaction, message, ephemeral=True)
    except Exception as error:
        await discord_helpers.error_message(interaction, error, ephemeral=True)
