"""Voting round domain model."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class VotingRoundStatus(StrEnum):
    """Lifecycle states for a voting round."""

    CREATED = "created"
    ACTIVE = "active"
    CLOSED = "closed"
    DECISION_GENERATED = "decision_generated"
    RESULTS_STORED = "results_stored"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class VotingRound:
    """One complete WFD meal-selection process."""

    id: str
    number: int
    created_at: datetime
    voting_deadline: datetime
    meals_required: int
    voter_ids: tuple[str, ...] = field(default_factory=tuple)
    closed_at: datetime | None = None
    status: VotingRoundStatus = VotingRoundStatus.CREATED

    @property
    def voter_count(self) -> int:
        """Return the number of participating voters recorded for the round."""
        return len(self.voter_ids)
