from database.database import Database
import errors.database_errors as DbErrors
from database.table_player import PlayerFields, PlayerRecord, PlayerTable
from database.table_team import TeamFields, TeamRecord, TeamTable
from database.table_team_player import (
    TeamPlayerFields,
    TeamPlayerRecord,
    TeamPlayerTable,
)


class RelatedRecords:
    """A class to manage related records in the database"""

    def __init__(self, database: Database):
        """Initialize the RelatedRecords class"""
        self.database: Database = database
        self.table_player = PlayerTable(database)
        self.table_team = TeamTable(database)
        self.table_team_player = TeamPlayerTable(database)

    async def get_team_from_player(self, player_record: PlayerRecord) -> TeamRecord:
        """Get the Team record associated with a Player record"""
        player_id = await player_record.get_field(PlayerFields.record_id)
        team_player_records = await self.table_team_player.get_team_player_records(
            player_id=player_id
        )
        if not team_player_records:
            return None
        team_id = await team_player_records[0].get_field(TeamPlayerFields.team_id)
        team_record = await self.table_team.get_team_record(record_id=team_id)
        return team_record

    async def get_player_records_from_team(
        self, team_record: TeamRecord
    ) -> list[PlayerRecord]:
        """Get the Player records associated with a Team record"""
        team_id = await team_record.get_field(TeamFields.record_id)
        team_player_records = await self.table_team_player.get_team_player_records(
            team_id=team_id
        )
        player_records = []
        for team_player_record in team_player_records:
            player_id = await team_player_record.get_field(TeamPlayerFields.player_id)
            player_record = await self.table_player.get_player_record(
                record_id=player_id
            )

            player_records.append(player_record)
        return player_records

    async def get_team_records_by_region(self, region: str) -> list[TeamRecord]:
        """Get the Team records associated with a region"""
        player_records = await self.table_player.get_players_by_region(region)
        team_player_records: list[TeamPlayerRecord] = []
        for player_record in player_records:
            player_id = await player_record.get_field(PlayerFields.record_id)
            team_player = self.table_team_player.get_team_player_records(
                player_id=player_id
            )
            team_player: TeamPlayerRecord = team_player[0] if team_player else None
            # We only use captains for this because they are 1:1 with teams
            if team_player and await team_player.get_field(TeamPlayerFields.is_captain):
                team_player_records.append(team_player)
        team_records: list[TeamRecord] = []
        for team_player_record in team_player_records:
            team_record = await self.table_team.get_team_record(
                team_id=await team_player_record.get_field(TeamPlayerFields.team_id)
            )
            team_records.append(team_record)
        return team_records

    async def create_new_team_with_captain(
        self, team_name: str, player: PlayerRecord
    ) -> TeamRecord:
        """Create a new Team with the given Captain"""
        new_team = await self.table_team.create_team_record(team_name)
        if not new_team:
            raise DbErrors.EmlRecordNotInserted(f"Failed to create Team: {team_name}")
        team_id = await new_team.get_field(TeamFields.record_id)
        player_id = await player.get_field(PlayerFields.record_id)
        new_team_player = await self.table_team_player.create_team_player_record(
            team_id=team_id,
            player_id=player_id,
            is_captain=True,
            is_co_captain=False,
        )
        if not new_team_player:
            raise DbErrors.EmlRecordNotInserted(
                f"Failed to create TeamPlayer for Team: {team_name}"
            )
        return new_team

    async def is_any_captain(self, player_record: PlayerRecord) -> bool:
        """Check if a Player is a Team Captain or Co-Captain"""
        team_player_records = await self.table_team_player.get_team_player_records(
            player_id=await player_record.get_field(PlayerFields.record_id)
        )
        for team_player_record in team_player_records:
            is_captain = await team_player_record.get_field(TeamPlayerFields.is_captain)
            is_co_captain = await team_player_record.get_field(
                TeamPlayerFields.is_co_captain
            )
            if is_captain or is_co_captain:
                return True
        return False

    async def is_main_captain(self, player_record: PlayerRecord) -> bool:
        """Check if a Player is a Team Captain or Co-Captain"""
        team_player_records = await self.table_team_player.get_team_player_records(
            player_id=await player_record.get_field(PlayerFields.record_id)
        )
        for team_player_record in team_player_records:
            is_captain = await team_player_record.get_field(TeamPlayerFields.is_captain)
            if is_captain:
                return True
        return False

    async def is_co_captain(self, player_record: PlayerRecord) -> bool:
        """Check if a Player is a Team Co-Captain"""
        team_player_records = await self.table_team_player.get_team_player_records(
            player_id=await player_record.get_field(PlayerFields.record_id)
        )
        for team_player_record in team_player_records:
            is_co_captain = await team_player_record.get_field(
                TeamPlayerFields.is_co_captain
            )
            if is_co_captain:
                return True
        return False

    async def is_player_on_a_team(self, player_record: PlayerRecord) -> bool:
        """Check if a Player is on a Team"""
        team_player_records = await self.table_team_player.get_team_player_records(
            player_id=await player_record.get_field(PlayerFields.record_id)
        )
        if team_player_records:
            return True
        return False
