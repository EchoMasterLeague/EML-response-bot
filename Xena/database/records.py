from database.enums import Bool, Regions, TeamStatus, MatchResult
from database.fields import (
    BaseFields,
    CommandLockFields,
    CooldownFields,
    ExampleFields,
    TeamInviteFields,
    MatchInviteFields,
    MatchResultInviteFields,
    MatchFields,
    PlayerFields,
    TeamFields,
    TeamPlayerFields,
    VwRosterFields,
)
from typing import Type
import errors.database_errors as DbErrors

### Base ###


class BaseRecord:
    """Record of a Database Table (row of the worksheet)

    Provides the following methods available to all tables:
    - `to_list()`: Return the record as a list of data (e.g. for `gsheets`)
    - `to_dict()`: Return the record as a dictionary
    - `get_field(field_enum)`: Get the value of a field
    - `set_field(field_enum, value)`: Set the value of a field
    """

    fields: Type[BaseFields]
    _data_dict: dict

    def __init__(
        self,
        data_list: list[int | float | str | None],
        fields: Type[BaseFields] = BaseFields,
    ):
        """Create a record from a list of data (e.g. from `gsheets`)"""
        self.fields = fields
        self._data_dict = {}
        for field in self.fields:
            self._data_dict[field.name] = data_list[field.value]

    async def to_list(self) -> list[int | float | str | None]:
        """Return the record as a list of data (e.g. for `gsheets`)"""
        data_list = [None] * len(self.fields)
        for field in self.fields:
            data_list[field.value] = self._data_dict[field.name]
        return data_list

    async def to_dict(self) -> dict:
        """Return the record as a dictionary"""
        return self._data_dict

    async def get_field(self, field_enum: int) -> int | float | str | None:
        """Get the value of a field"""
        for field in self.fields:
            if field.value == field_enum:
                return self._data_dict[field.name]
        raise ValueError(f"Field '{field_enum}' not found in '{self.fields}'")

    async def set_field(self, field_enum: int, value: int | float | str | None) -> None:
        """Set the value of a field"""
        for field in self.fields:
            if field.value == field_enum:
                self._data_dict[field.name] = value
                return
        raise ValueError(f"Field '{field_enum}' not found in '{self.fields}'")


### Examples ###


class ExampleRecord(BaseRecord):
    """Record class for table Example"""

    fields: Type[ExampleFields]

    def __init__(
        self,
        data_list: list[int | float | str | None],
        fields: Type[ExampleFields] = ExampleFields,
    ):
        """Create a record from a list of data (e.g. from `gsheets`)"""
        super().__init__(data_list, fields)


### Commands ###


class CommandLockRecord(BaseRecord):
    """Record class for table CommandLock"""

    fields: Type[CommandLockFields]

    def __init__(
        self,
        data_list: list[int | float | str | None],
        fields: Type[CommandLockFields] = CommandLockFields,
    ):
        """Create a record from a list of data (e.g. from `gsheets`)"""
        super().__init__(data_list, fields)
        # Conversion / Validation
        ## Is Allowed
        is_allowed = data_list[CommandLockFields.is_allowed.value]
        is_allowed = (
            True
            if (
                is_allowed == True
                or str(is_allowed).casefold() == str(Bool.TRUE).casefold()
            )
            else False
        )
        self._data_dict[CommandLockFields.is_allowed.name] = is_allowed

    async def to_list(self) -> list[int | float | str | None]:
        """Return the record as a list of data (e.g. for `gsheets`)"""
        data_list = await super().to_list()
        # Conversion
        is_allowed = self._data_dict[CommandLockFields.is_allowed.name]
        data_list[CommandLockFields.is_allowed.value] = (
            Bool.TRUE if is_allowed else Bool.FALSE
        )
        return data_list


### Roster ###
class VwRosterRecord(BaseRecord):
    """Record class for table VwRoster"""

    fields: Type[VwRosterFields]

    def __init__(
        self,
        data_list: list[int | float | str | None],
        fields: Type[VwRosterFields] = VwRosterFields,
    ):
        """Create a record from a list of data (e.g. from `gsheets`)"""
        super().__init__(data_list, fields)
        # Conversion / Validation
        ## Active
        active = data_list[VwRosterFields.active.value]
        active = (
            True
            if (active == True or str(active).casefold() == str(Bool.TRUE).casefold())
            else False
        )
        self._data_dict[VwRosterFields.active.name] = active

    async def to_list(self) -> list[int | float | str | None]:
        """Return the record as a list of data (e.g. for `gsheets`)"""
        data_list = await super().to_list()
        # Conversion
        active = self._data_dict[VwRosterFields.active.name]
        data_list[VwRosterFields.active.value] = Bool.TRUE if active else Bool.FALSE
        return data_list


### Players ###


class PlayerRecord(BaseRecord):
    """Record class for table Player"""

    fields: Type[PlayerFields]

    def __init__(
        self,
        data_list: list[int | float | str | None],
        fields: Type[PlayerFields] = PlayerFields,
    ):
        """Create a record from a list of data (e.g. from `gsheets`)"""
        super().__init__(data_list, fields)
        # Conversion / Validaton
        ## Discord ID
        discord_id = self._data_dict[PlayerFields.discord_id.name]
        self._data_dict[PlayerFields.discord_id.name] = str(discord_id)
        ## Region
        region = self._data_dict[PlayerFields.region.name]
        region_list = [r.value for r in Regions]
        for allowed_region in region_list:
            if str(region).casefold() == allowed_region.casefold():
                self._data_dict[PlayerFields.region.name] = allowed_region
                break
        if self._data_dict[PlayerFields.region.name] not in region_list:
            raise DbErrors.EmlRegionNotFound(
                f"Region '{region}' not available. Available Regions: {region_list}"
            )


class CooldownRecord(BaseRecord):
    """Record class for table Cooldown"""

    fields: Type[CooldownFields]

    def __init__(
        self,
        data_list: list[int | float | str | None],
        fields: Type[CooldownFields] = CooldownFields,
    ):
        """Create a record from a list of data (e.g. from `gsheets`)"""
        super().__init__(data_list, fields)


### Teams ###


class TeamRecord(BaseRecord):
    """Record class for table Team"""

    fields: Type[TeamFields]

    def __init__(
        self,
        data_list: list[int | float | str | None],
        fields: Type[TeamFields] = TeamFields,
    ):
        """Create a record from a list of data (e.g. from `gsheets`)"""
        super().__init__(data_list, fields)
        # Conversion / Validaton
        ## Status
        status = self._data_dict[TeamFields.status.name]
        allowed_status_list = [s.value for s in TeamStatus]
        for allowed_status in allowed_status_list:
            if str(status).casefold() == str(allowed_status).casefold():
                self._data_dict[TeamFields.status.name] = allowed_status
                break
        if self._data_dict[TeamFields.status.name] not in allowed_status_list:
            raise ValueError(
                f"Status '{status}' not available. Available Statuses: {allowed_status_list}"
            )


class TeamPlayerRecord(BaseRecord):
    """Record class for table TeamPlayer"""

    fields: Type[TeamPlayerFields]

    def __init__(
        self,
        data_list: list[int | float | str | None],
        fields: Type[TeamPlayerFields] = TeamPlayerFields,
    ):
        """Create a record from a list of data (e.g. from `gsheets`)"""
        super().__init__(data_list, fields)
        # Conversion / Validation
        ## Is Captain
        is_captain = data_list[TeamPlayerFields.is_captain.value]
        is_captain = (
            True
            if (
                is_captain == True
                or str(is_captain).casefold() == str(Bool.TRUE).casefold()
            )
            else False
        )
        self._data_dict[TeamPlayerFields.is_captain.name] = is_captain
        ## Is Co-Captain
        is_co_captain = data_list[TeamPlayerFields.is_co_captain.value]
        is_co_captain = (
            True
            if (
                is_co_captain == True
                or str(is_co_captain).casefold() == str(Bool.TRUE).casefold()
            )
            else False
        )
        self._data_dict[TeamPlayerFields.is_co_captain.name] = is_co_captain

    async def to_list(self) -> list[int | float | str | None]:
        """Return the record as a list of data (e.g. for `gsheets`)"""
        data_list = await super().to_list()
        # Conversion
        is_captain = self._data_dict[TeamPlayerFields.is_captain.name]
        data_list[TeamPlayerFields.is_captain.value] = (
            Bool.TRUE if is_captain else Bool.FALSE
        )
        is_co_captain = self._data_dict[TeamPlayerFields.is_co_captain.name]
        data_list[TeamPlayerFields.is_co_captain.value] = (
            Bool.TRUE if is_co_captain else Bool.FALSE
        )
        return data_list


class TeamInviteRecord(BaseRecord):
    """Record class for table TeamInvite"""

    fields: Type[TeamInviteFields]

    def __init__(
        self,
        data_list: list[int | float | str | None],
        fields: Type[TeamInviteFields] = TeamInviteFields,
    ):
        """Create a record from a list of data (e.g. from `gsheets`)"""
        super().__init__(data_list, fields)


### Matches ###


class MatchRecord(BaseRecord):
    """Record class for table Match"""

    fields: Type[MatchFields]

    def __init__(
        self,
        data_list: list[int | float | str | None],
        fields: Type[MatchFields] = MatchFields,
    ):
        """Create a record from a list of data (e.g. from `gsheets`)"""
        super().__init__(data_list, fields)
        # Conversion / Validation
        # ensure rounds are integers or null
        score_list = [
            data_list[MatchFields.round_1_score_a.value],
            data_list[MatchFields.round_1_score_b.value],
            data_list[MatchFields.round_2_score_a.value],
            data_list[MatchFields.round_2_score_b.value],
            data_list[MatchFields.round_3_score_a.value],
            data_list[MatchFields.round_3_score_b.value],
        ]
        new_score_list = []
        for score in score_list:
            if score == "" or score is None:
                new_score_list.append(None)
            else:
                new_score_list.append(int(score))
        self._data_dict[MatchFields.round_1_score_a.name] = new_score_list[0]
        self._data_dict[MatchFields.round_1_score_b.name] = new_score_list[1]
        self._data_dict[MatchFields.round_2_score_a.name] = new_score_list[2]
        self._data_dict[MatchFields.round_2_score_b.name] = new_score_list[3]
        self._data_dict[MatchFields.round_3_score_a.name] = new_score_list[4]
        self._data_dict[MatchFields.round_3_score_b.name] = new_score_list[5]

    async def to_list(self) -> list[int | float | str | None]:
        """Return the record as a list of data (e.g. for `gsheets`)"""
        data_list = await super().to_list()
        # Conversion
        score_list = [
            data_list[MatchFields.round_1_score_a.value],
            data_list[MatchFields.round_1_score_b.value],
            data_list[MatchFields.round_2_score_a.value],
            data_list[MatchFields.round_2_score_b.value],
            data_list[MatchFields.round_3_score_a.value],
            data_list[MatchFields.round_3_score_b.value],
        ]
        new_score_list = []
        for score in score_list:
            if score == "" or score is None:
                new_score_list.append(None)
            else:
                new_score_list.append(int(score))
        data_list[MatchFields.round_1_score_a.value] = new_score_list[0]
        data_list[MatchFields.round_1_score_b.value] = new_score_list[1]
        data_list[MatchFields.round_2_score_a.value] = new_score_list[2]
        data_list[MatchFields.round_2_score_b.value] = new_score_list[3]
        data_list[MatchFields.round_3_score_a.value] = new_score_list[4]
        data_list[MatchFields.round_3_score_b.value] = new_score_list[5]
        return data_list

    async def set_scores(self, scores: list[list[int | None]]) -> None:
        """Set the scores of the match
        from the form of `scores[round][team] = score`
        """
        self._data_dict[MatchFields.round_1_score_a.name] = scores[0][0]
        self._data_dict[MatchFields.round_1_score_b.name] = scores[0][1]
        self._data_dict[MatchFields.round_2_score_a.name] = scores[1][0]
        self._data_dict[MatchFields.round_2_score_b.name] = scores[1][1]
        self._data_dict[MatchFields.round_3_score_a.name] = scores[2][0]
        self._data_dict[MatchFields.round_3_score_b.name] = scores[2][1]

    async def get_scores(self) -> list[list[int | None]]:
        """Return the scores of the match
        in the form of `scores[round][team] = score`
        """
        scores = [
            [
                self._data_dict[MatchFields.round_1_score_a.name],
                self._data_dict[MatchFields.round_1_score_b.name],
            ],
            [
                self._data_dict[MatchFields.round_2_score_a.name],
                self._data_dict[MatchFields.round_2_score_b.name],
            ],
            [
                self._data_dict[MatchFields.round_3_score_a.name],
                self._data_dict[MatchFields.round_3_score_b.name],
            ],
        ]
        return scores


class MatchInviteRecord(BaseRecord):
    """Record class for table MatchInvite"""

    fields: Type[MatchInviteFields]

    def __init__(
        self,
        data_list: list[int | float | str | None],
        fields: Type[MatchInviteFields] = MatchInviteFields,
    ):
        """Create a record from a list of data (e.g. from `gsheets`)"""
        super().__init__(data_list, fields)


class MatchResultInviteRecord(BaseRecord):
    """Record class for table MatchResultInvite"""

    fields: Type[MatchResultInviteFields]

    def __init__(
        self,
        data_list: list[int | float | str | None],
        fields: Type[MatchResultInviteFields] = MatchResultInviteFields,
    ):
        """Create a record from a list of data (e.g. from `gsheets`)"""
        super().__init__(data_list, fields)
        # Conversion / Validation
        # ensure rounds are integers or null
        score_list = [
            data_list[MatchResultInviteFields.round_1_score_a.value],
            data_list[MatchResultInviteFields.round_1_score_b.value],
            data_list[MatchResultInviteFields.round_2_score_a.value],
            data_list[MatchResultInviteFields.round_2_score_b.value],
            data_list[MatchResultInviteFields.round_3_score_a.value],
            data_list[MatchResultInviteFields.round_3_score_b.value],
        ]
        new_score_list = []
        for score in score_list:
            if score == "" or score is None:
                new_score_list.append(None)
            else:
                new_score_list.append(int(score))
        self._data_dict[MatchResultInviteFields.round_1_score_a.name] = new_score_list[
            0
        ]
        self._data_dict[MatchResultInviteFields.round_1_score_b.name] = new_score_list[
            1
        ]
        self._data_dict[MatchResultInviteFields.round_2_score_a.name] = new_score_list[
            2
        ]
        self._data_dict[MatchResultInviteFields.round_2_score_b.name] = new_score_list[
            3
        ]
        self._data_dict[MatchResultInviteFields.round_3_score_a.name] = new_score_list[
            4
        ]
        self._data_dict[MatchResultInviteFields.round_3_score_b.name] = new_score_list[
            5
        ]

    async def to_list(self) -> list[int | float | str | None]:
        """Return the record as a list of data (e.g. for `gsheets`)"""
        data_list = await super().to_list()
        # Conversion
        score_list = [
            data_list[MatchResultInviteFields.round_1_score_a.value],
            data_list[MatchResultInviteFields.round_1_score_b.value],
            data_list[MatchResultInviteFields.round_2_score_a.value],
            data_list[MatchResultInviteFields.round_2_score_b.value],
            data_list[MatchResultInviteFields.round_3_score_a.value],
            data_list[MatchResultInviteFields.round_3_score_b.value],
        ]
        new_score_list = []
        for score in score_list:
            if score == "" or score is None:
                new_score_list.append(None)
            else:
                new_score_list.append(int(score))
        data_list[MatchResultInviteFields.round_1_score_a.value] = new_score_list[0]
        data_list[MatchResultInviteFields.round_1_score_b.value] = new_score_list[1]
        data_list[MatchResultInviteFields.round_2_score_a.value] = new_score_list[2]
        data_list[MatchResultInviteFields.round_2_score_b.value] = new_score_list[3]
        data_list[MatchResultInviteFields.round_3_score_a.value] = new_score_list[4]
        data_list[MatchResultInviteFields.round_3_score_b.value] = new_score_list[5]
        return data_list

    async def get_scores(self) -> list[list[int | None]]:
        """Return the scores of the match
        in the form of `scores[round][team] = score`
        """
        scores = [
            [
                self._data_dict[MatchResultInviteFields.round_1_score_a.name],
                self._data_dict[MatchResultInviteFields.round_1_score_b.name],
            ],
            [
                self._data_dict[MatchResultInviteFields.round_2_score_a.name],
                self._data_dict[MatchResultInviteFields.round_2_score_b.name],
            ],
            [
                self._data_dict[MatchResultInviteFields.round_3_score_a.name],
                self._data_dict[MatchResultInviteFields.round_3_score_b.name],
            ],
        ]
        return scores
