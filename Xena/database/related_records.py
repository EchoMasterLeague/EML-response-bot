from database.database import Database
import database.table_player as Player
import database.table_team as Team
import database.table_team_player as TeamPlayer
import errors.database_errors as DbErrors


class RelatedRecords:
    """A class to manage related records in the database"""

    def __init__(self, database: Database):
        """Initialize the RelatedRecords class"""
        self.database: Database = database
        self.table_player = Player.PlayerTable(database)
        self.table_team = Team.TeamTable(database)
        self.table_team_player = TeamPlayer.TeamPlayerTable(database)

    async def get_team_from_player(
        self, player_record: Player.PlayerRecord
    ) -> Team.TeamRecord:
        """Get the Team record associated with a Player record"""
        player_id = await player_record.get_field(Player.PlayerFields.RECORD_ID.name)
        team_player_records = await self.table_team_player.get_team_player_records(
            player_id=player_id
        )
        if not team_player_records:
            raise DbErrors.EmlTeamPlayerNotFound(
                f"TeamPlayer record not found for Player: {player_record.to_dict()}"
            )
        team_id = await team_player_records[0].get_field(
            TeamPlayer.TeamPlayerFields.TEAM_ID.name
        )
        team_record = await self.table_team.get_team(record_id=team_id)
        if not team_record:
            raise DbErrors.EmlTeamNotFound(
                f"Team record not found for TeamPlayer[0]: {team_player_records}"
            )
        return team_record

    async def get_player_records_from_team(
        self, team_record: Team.TeamRecord
    ) -> list[Player.PlayerRecord]:
        """Get the Player records associated with a Team record"""
        team_id = await team_record.get_field(Team.TeamFields.RECORD_ID.name)
        team_player_records = await self.table_team_player.get_team_player_records(
            team_id=team_id
        )
        if not team_player_records:
            raise DbErrors.EmlTeamPlayerNotFound(
                f"TeamPlayer records not found for Team: {team_record.to_dict()}"
            )
        player_records = []
        for team_player_record in team_player_records:
            team_player_id = await team_player_record.get_field(
                TeamPlayer.TeamPlayerFields.RECORD_ID.name
            )
            player_record = await self.table_player.get_player_record(
                record_id=team_player_id
            )
            if not player_record:
                raise DbErrors.EmlPlayerNotFound(
                    f"Player record not found for TeamPlayer: {team_player_record.to_dict()}"
                )
            player_records.append(player_record)
        if not player_records:
            raise DbErrors.EmlPlayerNotFound(
                f"Player records not found for Team: {team_record.to_dict()}"
            )
        return player_records

    async def get_team_records_by_region(self, region: str) -> list[Team.TeamRecord]:
        """Get the Team records associated with a region"""
        player_records = await self.table_player.get_players_by_region(region)
        if not player_records:
            raise DbErrors.EmlPlayerNotFound(
                f"Player records not found for region: {region}"
            )
        team_player_records: list[TeamPlayer.TeamPlayerRecord] = []
        for player_record in player_records:
            player_id = await player_record.get_field(
                Player.PlayerFields.RECORD_ID.name
            )
            team_player = self.table_team_player.get_team_player_records(
                player_id=player_id
            )
            if not team_player:
                raise DbErrors.EmlTeamPlayerNotFound(
                    f"TeamPlayer record not found for Player: {player_record.to_dict()}"
                )
            team_player: TeamPlayer.TeamPlayerRecord = (
                team_player[0] if team_player else None
            )
            # We only use captains for this because they are 1:1 with teams
            if team_player and await team_player.get_field(
                TeamPlayer.TeamPlayerFields.IS_CAPTAIN.name
            ):
                team_player_records.append(team_player)
        if not team_player_records:
            raise DbErrors.EmlTeamPlayerNotFound(
                f"TeamPlayer records not found for region: {region}"
            )
        team_records: list[Team.TeamRecord] = []
        for team_player_record in team_player_records:
            team_record = await self.table_team.get_team(
                team_id=await team_player_record.get_field(
                    TeamPlayer.TeamPlayerFields.TEAM_ID.name
                )
            )
            if not team_record:
                raise DbErrors.EmlTeamNotFound(
                    f"Team record not found for TeamPlayer: {team_player_record.to_dict()}"
                )
            team_records.append(team_record)
        if not team_records:
            raise DbErrors.EmlTeamNotFound(
                f"Team records not found for region: {region}"
            )
        return team_records

    async def create_new_team_with_captain(
        self, team_name: str, player: Player.PlayerRecord
    ) -> Team.TeamRecord:
        """Create a new Team with the given Captain"""
        new_team = await self.table_team.create_team(team_name)
        if not new_team:
            raise DbErrors.EmlTeamNotCreated(f"Failed to create Team: {team_name}")
        team_id = await new_team.get_field(Team.TeamFields.RECORD_ID.name)
        player_id = await player.get_field(Player.PlayerFields.RECORD_ID.name)
        new_team_player = await self.table_team_player.create_team_player_record(
            team_id=team_id,
            player_id=player_id,
            is_captain=True,
            is_co_captain=False,
        )
        if not new_team_player:
            raise DbErrors.EmlTeamPlayerNotCreated(
                f"Failed to create TeamPlayer for Team: {team_name}"
            )
        return new_team

    async def is_any_captain(self, player_record: Player.PlayerRecord) -> bool:
        """Check if a Player is a Team Captain or Co-Captain"""
        team_player_records = await self.table_team_player.get_team_player_records(
            player_id=await player_record.get_field(Player.PlayerFields.RECORD_ID.name)
        )
        for team_player_record in team_player_records:
            is_captain = await team_player_record.get_field(
                TeamPlayer.TeamPlayerFields.IS_CAPTAIN.name
            )
            is_co_captain = await team_player_record.get_field(
                TeamPlayer.TeamPlayerFields.IS_CO_CAPTAIN.name
            )
            if is_captain or is_co_captain:
                return True
        return False

    async def is_main_captain(self, player_record: Player.PlayerRecord) -> bool:
        """Check if a Player is a Team Captain or Co-Captain"""
        team_player_records = await self.table_team_player.get_team_player_records(
            player_id=await player_record.get_field(Player.PlayerFields.RECORD_ID.name)
        )
        for team_player_record in team_player_records:
            is_captain = await team_player_record.get_field(
                TeamPlayer.TeamPlayerFields.IS_CAPTAIN.name
            )
            if is_captain:
                return True
        return False

    async def is_co_captain(self, player_record: Player.PlayerRecord) -> bool:
        """Check if a Player is a Team Co-Captain"""
        team_player_records = await self.table_team_player.get_team_player_records(
            player_id=await player_record.get_field(Player.PlayerFields.RECORD_ID.name)
        )
        for team_player_record in team_player_records:
            is_co_captain = await team_player_record.get_field(
                TeamPlayer.TeamPlayerFields.IS_CO_CAPTAIN.name
            )
            if is_co_captain:
                return True
        return False

    async def is_player_on_a_team(self, player_record: Player.PlayerRecord) -> bool:
        """Check if a Player is on a Team"""
        team_player_records = await self.table_team_player.get_team_player_records(
            player_id=await player_record.get_field(Player.PlayerFields.RECORD_ID.name)
        )
        if team_player_records:
            return True
        return False
