from database.base_table import BaseTable
from database.database_core import CoreDatabase
from database.fields import VwRosterFields
from database.records import VwRosterRecord
import constants
import errors.database_errors as DbErrors
import gspread
import utils.general_helpers as general_helpers
from database.enums import MatchType, MatchStatus


"""
VwRoster Table
"""


class VwRosterTable(BaseTable):
    """A class to manipulate the Match table in the database"""

    _db: CoreDatabase
    _worksheet: gspread.Worksheet

    def __init__(self, db: CoreDatabase):
        """Initialize the Match Table class"""
        super().__init__(
            db, constants.LEAGUE_DB_TAB_VW_ROSTER, VwRosterRecord, VwRosterFields
        )

    async def create_vw_roster_record(
        self,
        team_id: str,
        team_name: str,
        captain_name: str,
        co_captain_name: str,
        player_names: list[str],
    ) -> VwRosterRecord:
        """Create a new Match record"""
        # Sort player names and remove captains
        player_names = sorted(player_names)
        # Remove captains from the list if they exist

        if captain_name in player_names:
            player_names.remove(captain_name)
        if co_captain_name in player_names:
            player_names.remove(co_captain_name)
        if not co_captain_name:
            co_captain_name = player_names.pop(0) if player_names else None
        total_players = len(player_names)
        total_players += 1 if captain_name else 0
        total_players += 1 if co_captain_name else 0
        is_active = True
        if total_players < constants.TEAM_PLAYERS_MIN:
            is_active = False
        # Check for existing records to avoid duplication
        existing_records = await self.get_vw_roster_records(
            record_id=team_id,
            team_name=team_name,
        )
        if existing_records:
            # Update the existing record
            existing_record = existing_records[0]
            await existing_record.set_field(VwRosterFields.team, team_name)
            await existing_record.set_field(VwRosterFields.captain, captain_name)
            await existing_record.set_field(VwRosterFields.co_cap_or_2, co_captain_name)
            await existing_record.set_field(
                VwRosterFields.player_3, player_names.pop(0) if player_names else None
            )
            await existing_record.set_field(
                VwRosterFields.player_4, player_names.pop(0) if player_names else None
            )
            await existing_record.set_field(
                VwRosterFields.player_5, player_names.pop(0) if player_names else None
            )
            await existing_record.set_field(
                VwRosterFields.player_6, player_names.pop(0) if player_names else None
            )
            await existing_record.set_field(VwRosterFields.active, is_active)
            await self.update_vw_roster_record(existing_record)
            return existing_record
        # Create a new record
        record_list = [None] * len(VwRosterFields)
        record_list[VwRosterFields.team] = team_name
        record_list[VwRosterFields.captain] = captain_name
        record_list[VwRosterFields.co_cap_or_2] = co_captain_name
        record_list[VwRosterFields.player_3] = (
            player_names.pop(0) if player_names else None
        )
        record_list[VwRosterFields.player_4] = (
            player_names.pop(0) if player_names else None
        )
        record_list[VwRosterFields.player_5] = (
            player_names.pop(0) if player_names else None
        )
        record_list[VwRosterFields.player_6] = (
            player_names.pop(0) if player_names else None
        )
        record_list[VwRosterFields.active] = is_active
        new_record = await self.create_record(record_list, VwRosterFields)
        await new_record.set_field(VwRosterFields.record_id, team_id)
        # Insert the new record into the database
        await self.insert_record(new_record)
        return new_record

    async def update_vw_roster_record(self, record: VwRosterRecord) -> None:
        """Update an existing Player record"""
        await self.update_record(record)

    async def delete_vw_roster_record(self, record: VwRosterRecord) -> None:
        """Delete an existing Player record"""
        record_id = await record.get_field(VwRosterFields.record_id)
        await self.delete_record(record_id)

    async def get_vw_roster_records(
        self,
        record_id: str = None,
        team_name: str = None,
    ) -> list[VwRosterRecord]:
        """Get existing VwRoster records"""
        if record_id is None and team_name is None:
            raise ValueError("Must provide either record_id or team_name")
        table = await self.get_table_data()
        existing_records: list[VwRosterRecord] = []
        for row in table:
            if table.index(row) == 0:
                continue
            if (
                not record_id
                or str(record_id).casefold()
                == str(row[VwRosterFields.record_id]).casefold()
            ) and (
                not team_name
                or str(team_name).casefold() == str(row[VwRosterFields.team]).casefold()
            ):
                existing_records.append(VwRosterRecord(row))
        return existing_records

    async def delete_all_vw_roster_records(self) -> None:
        """Delete all VwRoster records"""
        self._tab.clear()
        return

    async def write_all_vw_roster_records(
        self, roster_table: list[list[int | float | str | None]]
    ) -> None:
        """Write a list of VwRoster records to the database"""
        await self.delete_all_vw_roster_records()
        self._tab.append_rows(roster_table)
        return
