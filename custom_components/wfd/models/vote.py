"""Vote domain model."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Vote:
    """A private vote cast by a user for a meal in a round."""

    round_id: str
    user_id: str
    meal_id: str
