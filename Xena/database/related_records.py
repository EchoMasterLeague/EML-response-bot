from database.database import Database
import database.table_player as Player
import database.table_team as Team
import database.table_team_player as TeamPlayer


class RelatedRecords:
    """A class to manage related records in the database"""

    def __init__(self, database: Database):
        """Initialize the RelatedRecords class"""
        self.database: Database = database
        self.table_player = Player.Action(database)
        self.table_team = Team.Action(database)
        self.table_team_player = TeamPlayer.Action(database)

    async def get_team_from_player(self, player_record: Player.Record) -> Team.Record:
        """Get the Team record associated with a Player record"""
        team_player_records = await self.table_team_player.get_team_player_records(
            player_id=player_record.to_dict()[Player.Field.record_id.name]
        )
        if not team_player_records:
            return None
        team_record = await self.table_team.get_team(
            team_id=team_player_records[0].to_dict()[TeamPlayer.Field.team_id.name]
        )
        return team_record

    async def get_player_records_from_team(
        self, team_record: Team.Record
    ) -> list[Player.Record]:
        """Get the Player records associated with a Team record"""
        team_player_records = await self.table_team_player.get_team_player_records(
            team_id=team_record.to_dict()[Team.Field.record_id.name]
        )
        player_records = []
        for team_player_record in team_player_records:
            player_record = await self.table_player.get_player(
                record_id=team_player_record.to_dict()[TeamPlayer.Field.player_id.name]
            )
            player_records.append(player_record)
        return player_records

    async def get_team_records_by_region(self, region: str) -> list[Team.Record]:
        """Get the Team records associated with a region"""
        player_records_in_region = await self.table_player.get_players_by_region(region)
        captain_team_player_records_in_region: list[TeamPlayer.Record] = []
        for player_record in player_records_in_region:
            team_player = self.table_team_player.get_team_player_records(
                player_id=player_record.to_dict()[Player.Field.record_id.name]
            )
            team_player: TeamPlayer.Record = team_player[0] if team_player else None
            if team_player and team_player.to_dict()[TeamPlayer.Field.is_captain.name]:
                captain_team_player_records_in_region.append(team_player)
        team_records_in_region: list[Team.Record] = []
        for team_player_record in captain_team_player_records_in_region:
            team_record = await self.table_team.get_team(
                team_id=team_player_record.to_dict()[TeamPlayer.Field.team_id.name]
            )
            team_records_in_region.append(team_record)
        return team_records_in_region

    async def create_new_team_with_captain(
        self, team_name: str, player: Player.Record
    ) -> Team.Record:
        """Create a new Team with the given Captain"""
        new_team = await self.table_team.create_team(team_name)
        if not new_team:
            return None
        new_team_player = await self.table_team_player.create_team_player(
            new_team.to_dict()[Team.Field.record_id.name],
            player.to_dict()[Player.Field.record_id.name],
            is_captain=True,
            is_co_captain=False,
        )
        if not new_team_player:
            return None
        return new_team

    async def is_captain(self, player_record: Player.Record) -> bool:
        """Check if a Player is a Team Captain"""
        team_player_records = await self.table_team_player.get_team_player_records(
            player_id=player_record.to_dict()[Player.Field.record_id.name]
        )
        if not team_player_records:
            return False
        for team_player_record in team_player_records:
            if (
                TeamPlayer.Bool.TRUE.value
                == team_player_record.to_dict()[TeamPlayer.Field.is_captain.name]
            ):
                return True
        return False

    async def is_co_captain(self, player_record: Player.Record) -> bool:
        """Check if a Player is a Team Co-Captain"""
        team_player_records = await self.table_team_player.get_team_player_records(
            player_id=player_record.to_dict()[Player.Field.record_id.name]
        )
        if not team_player_records:
            return False
        for team_player_record in team_player_records:
            if (
                TeamPlayer.Bool.TRUE.value
                == team_player_record.to_dict()[TeamPlayer.Field.is_co_captain.name]
            ):
                return True
        return False

    async def is_any_captain(self, player_record: Player.Record) -> bool:
        """Check if a Player is a Team Captain or Co-Captain"""
        team_player_records = await self.table_team_player.get_team_player_records(
            player_id=player_record.to_dict()[Player.Field.record_id.name]
        )
        if not team_player_records:
            return False
        for team_player_record in team_player_records:
            if (
                TeamPlayer.Bool.TRUE.value
                == team_player_record.to_dict()[TeamPlayer.Field.is_captain.name]
                or TeamPlayer.Bool.TRUE.value
                == team_player_record.to_dict()[TeamPlayer.Field.is_co_captain.name]
            ):
                return True
        return False
