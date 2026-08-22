"""Persistent storage for WFD domain data."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .models import Meal, RoundResult, User, Vote, VotingRound
from .models.voting_round import VotingRoundStatus

STORAGE_VERSION = 1
STORAGE_KEY = "wfd.storage"


class WFDStorage:
    """Persist and retrieve WFD domain data using Home Assistant storage."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialise WFD persistent storage."""
        self._store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            STORAGE_KEY,
        )
        self._data: dict[str, Any] = self._empty_data()

    @staticmethod
    def _empty_data() -> dict[str, Any]:
        """Return the initial storage structure."""
        return {
            "users": {},
            "meals": {},
            "rounds": {},
            "votes": [],
            "results": [],
        }

    async def async_load(self) -> None:
        """Load persisted data, or initialise an empty store."""
        data = await self._store.async_load()
        self._data = data or self._empty_data()

    async def async_save(self) -> None:
        """Persist the current data."""
        await self._store.async_save(self._data)

    async def async_set_user(self, user: User) -> None:
        """Create or update a user."""
        self._data["users"][user.id] = asdict(user)
        await self.async_save()

    async def async_set_meal(self, meal: Meal) -> None:
        """Create or update a meal."""
        self._data["meals"][meal.id] = asdict(meal)
        await self.async_save()

    async def async_set_voting_round(self, voting_round: VotingRound) -> None:
        """Create or update a voting round, protecting completed rounds."""
        existing = self._data["rounds"].get(voting_round.id)
        if existing and existing["status"] in {
            VotingRoundStatus.CLOSED,
            VotingRoundStatus.DECISION_GENERATED,
            VotingRoundStatus.RESULTS_STORED,
        }:
            raise ValueError("Completed voting rounds are immutable")

        self._data["rounds"][voting_round.id] = _serialize_round(voting_round)
        await self.async_save()

    async def async_add_vote(self, vote: Vote) -> None:
        """Persist a vote, rejecting duplicate user/meal votes in a round."""
        if any(
            item["round_id"] == vote.round_id
            and item["user_id"] == vote.user_id
            and item["meal_id"] == vote.meal_id
            for item in self._data["votes"]
        ):
            raise ValueError("Duplicate vote")

        self._data["votes"].append(asdict(vote))
        await self.async_save()

    async def async_add_result(self, result: RoundResult) -> None:
        """Persist a round result."""
        self._data["results"].append(asdict(result))
        await self.async_save()


def _serialize_round(voting_round: VotingRound) -> dict[str, Any]:
    """Serialise a voting round into JSON-compatible values."""
    data = asdict(voting_round)
    data["created_at"] = voting_round.created_at.isoformat()
    data["voting_deadline"] = voting_round.voting_deadline.isoformat()
    data["closed_at"] = (
        voting_round.closed_at.isoformat() if voting_round.closed_at else None
    )
    data["voter_ids"] = list(voting_round.voter_ids)
    data["status"] = voting_round.status.value
    return data
