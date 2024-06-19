from enum import EnumCheck, StrEnum, verify
import logging

logger = logging.getLogger(__name__)

### Database ###


@verify(EnumCheck.UNIQUE)
class WriteOperations(StrEnum):
    """Lookup for Write Operation values"""

    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


### Common ###


@verify(EnumCheck.UNIQUE)
class Bool(StrEnum):
    """Lookup for Truthy values"""

    TRUE = "Yes"
    FALSE = "No"


### Invites ###


@verify(EnumCheck.UNIQUE)
class InviteStatus(StrEnum):
    """Lookup for Invite Status values"""

    PENDING = "Pending"  # The invite has not been accepted or declined
    ACCEPTED = "Accepted"  # The invite has been accepted
    DECLINED = "Declined"  # The invite has been declined
    REVOKED = "Revoked"  # The invite has been revoked


### Players ###


@verify(EnumCheck.UNIQUE)
class Regions(StrEnum):
    """Lookup for Region values"""

    NA = "NA"  # North America
    EU = "EU"  # Europe
    OCE = "OCE"  # Oceanic


### Teams ###


@verify(EnumCheck.UNIQUE)
class TeamStatus(StrEnum):
    """Lookup for Status values (e.g. in the Team table)"""

    ACTIVE = "Active"  # The team is active
    INACTIVE = "Inactive"  # The team is inactive


### Matches ###


@verify(EnumCheck.UNIQUE)
class MatchStatus(StrEnum):
    """Lookup for Match Status values"""

    PENDING = "Pending"  # The match has not been played
    COMPLETED = "Completed"  # The match was played
    ABANDONED = "Abandoned"  # The match was not played
    FORFEITED = "Forfeited"  # One team did not show up


@verify(EnumCheck.UNIQUE)
class MatchType(StrEnum):
    """Lookup for Match Type values"""

    ASSIGNED = "Assigned"  # Match Assigned by EML
    POSTPONED = "Postponed"  # Assigned match was delayed
    CHALLENGE = "Challenge"  # The invite kind, teams do themselves


@verify(EnumCheck.UNIQUE)
class MatchResult(StrEnum):
    """Lookup for Match Result values"""

    WIN = "Win"  # Team A won the match (Team B lost)
    LOSS = "Loss"  # Team A lost the match (Team B won)
    DRAW = "Draw"  # The match was a draw
