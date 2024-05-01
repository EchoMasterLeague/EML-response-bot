from enum import IntEnum, EnumCheck, StrEnum, verify


@verify(EnumCheck.UNIQUE)
class Bool(StrEnum):
    """Lookup for Truthy values"""

    TRUE = "Yes"
    FALSE = "No"


@verify(EnumCheck.UNIQUE)
class Regions(StrEnum):
    """Lookup for Region values"""

    NA = "NA"  # North America
    EU = "EU"  # Europe
    OCE = "OCE"  # Oceanic


@verify(EnumCheck.UNIQUE)
class TeamStatus(StrEnum):
    """Lookup for Status values (e.g. in the Team table)"""

    ACTIVE = "Active"  # The team is active
    INACTIVE = "Inactive"  # The team is inactive
