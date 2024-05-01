from database.enums import Bool, Regions, TeamStatus
from database.fields import (
    BaseFields,
    CommandLockFields,
    CooldownFields,
    ExampleFields,
    InviteFields,
    PlayerFields,
    TeamFields,
    TeamPlayerFields,
)
from typing import Type
import errors.database_errors as DbErrors


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


class ExampleRecord(BaseRecord):
    """Record class for this table"""

    fields: Type[ExampleFields]
    _data_dict: dict

    def __init__(self, data_list: list[int | float | str | None]):
        """Create a record from a list of data (e.g. from `gsheets`)"""
        super().__init__(ExampleFields, data_list)


class CommandLockRecord(BaseRecord):
    """Record class for this table"""

    fields: Type[CommandLockFields]
    _data_dict: dict

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


class CooldownRecord(BaseRecord):
    """Record class for this table"""

    fields: Type[CooldownFields]
    _data_dict: dict

    def __init__(
        self,
        data_list: list[int | float | str | None],
        fields: Type[CooldownFields] = CooldownFields,
    ):
        """Create a record from a list of data (e.g. from `gsheets`)"""
        super().__init__(data_list, fields)


class InviteRecord(BaseRecord):
    """Record class for this table"""

    fields: Type[InviteFields]
    _data_dict: dict

    def __init__(
        self,
        data_list: list[int | float | str | None],
        fields: Type[InviteFields] = InviteFields,
    ):
        """Create a record from a list of data (e.g. from `gsheets`)"""
        super().__init__(data_list, fields)


class PlayerRecord(BaseRecord):
    """Record class for this table"""

    fields: Type[PlayerFields]
    _data_dict: dict

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


class TeamPlayerRecord(BaseRecord):
    """Record class for this table"""

    fields: Type[TeamPlayerFields]
    _data_dict: dict

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


class TeamRecord(BaseRecord):
    """Record class for this table"""

    fields: Type[TeamFields]
    _data_dict: dict

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
