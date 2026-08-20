"""Voting round result domain model."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RoundResult:
    """Decision-engine output for one meal within a completed round."""

    round_id: str
    meal_id: str
    selected: bool
    decision_score: float
    vote_score: float
    historical_score: float
    recency_score: float
    rank: int
    explanation: str

    @property
    def selection_status(self) -> str:
        """Return a stable human-readable selection state."""
        return "selected" if self.selected else "not_selected"
