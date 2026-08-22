"""Persistent storage for WFD domain data."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import TYPE_CHECKING, Any

from .migrations import CURRENT_SCHEMA_VERSION, migrate
from .models import Meal, RoundResult, User, Vote, VotingRound
from .models.voting_round import VotingRoundStatus

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.storage import Store

STORAGE_VERSION = CURRENT_SCHEMA_VERSION
STORAGE_KEY = "wfd.storage"


class WFDStorage:
    """Persist and retrieve WFD domain data using Home Assistant storage."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialise WFD persistent storage."""
        from homeassistant.helpers.storage import Store

        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._data: dict[str, Any] = self._empty_data()

    @staticmethod
    def _empty_data() -> dict[str, Any]:
        """Return the initial storage structure."""
        return {"users": {}, "meals": {}, "rounds": {}, "votes": [], "results": []}

    async def async_load(self) -> None:
        """Load persisted data, migrating legacy data when required."""
        data = await self._store.async_load()
        if data is None:
            self._data = self._empty_data()
            return
        self._data = migrate(data, STORAGE_VERSION)

    async def async_save(self) -> None:
        """Persist the current data."""
        await self._store.async_save(self._data)

    async def async_set_user(self, user: User) -> None:
        """Create or update a voter backed by a Home Assistant Person."""
        self._data["users"][user.id] = asdict(user)
        await self.async_save()

    async def async_get_user(self, user_id: str) -> User | None:
        """Return a voter by Home Assistant Person ID."""
        data = self._data["users"].get(user_id)
        return deserialize_user(data) if data is not None else None

    async def async_get_users(self) -> list[User]:
        """Return all persisted WFD voters."""
        return [deserialize_user(data) for data in self._data["users"].values()]

    async def async_set_meal(self, meal: Meal) -> None:
        """Create or update a meal."""
        self._data["meals"][meal.id] = asdict(meal)
        await self.async_save()

    async def async_get_meal(self, meal_id: str) -> Meal | None:
        """Return a meal by ID, or None when it does not exist."""
        data = self._data["meals"].get(meal_id)
        return deserialize_meal(data) if data is not None else None

    async def async_get_meals(self) -> list[Meal]:
        """Return all persisted meals as domain objects."""
        return [deserialize_meal(data) for data in self._data["meals"].values()]

    async def async_set_voting_round(self, voting_round: VotingRound) -> None:
        """Create or update a voting round, protecting completed rounds."""
        existing = self._data["rounds"].get(voting_round.id)
        if existing and existing["status"] in {
            VotingRoundStatus.CLOSED.value,
            VotingRoundStatus.DECISION_GENERATED.value,
            VotingRoundStatus.RESULTS_STORED.value,
        }:
            raise ValueError("Completed voting rounds are immutable")
        self._data["rounds"][voting_round.id] = _serialize_round(voting_round)
        await self.async_save()

    async def async_add_vote(self, vote: Vote) -> None:
        """Persist a vote after validating its round, voter and meal."""
        round_data = self._data["rounds"].get(vote.round_id)
        if round_data is None:
            raise ValueError("Unknown voting round")
        if round_data["status"] != VotingRoundStatus.ACTIVE.value:
            raise ValueError("Votes can only be added to active rounds")
        if vote.user_id not in round_data["voter_ids"]:
            raise ValueError("User is not a voter in this round")
        if vote.user_id not in self._data["users"]:
            raise ValueError("Unknown user")
        if vote.meal_id not in self._data["meals"]:
            raise ValueError("Unknown meal")
        if not self._data["meals"][vote.meal_id]["active"]:
            raise ValueError("Meal is inactive")
        if any(item["round_id"] == vote.round_id and item["user_id"] == vote.user_id and item["meal_id"] == vote.meal_id for item in self._data["votes"]):
            raise ValueError("Duplicate vote")
        self._data["votes"].append(asdict(vote))
        await self.async_save()

    async def async_add_result(self, result: RoundResult) -> None:
        """Persist a round result after validating its source round and meal."""
        round_data = self._data["rounds"].get(result.round_id)
        if round_data is None:
            raise ValueError("Unknown voting round")
        if round_data["status"] not in {VotingRoundStatus.DECISION_GENERATED.value, VotingRoundStatus.RESULTS_STORED.value}:
            raise ValueError("Results can only be added after decision generation")
        if result.meal_id not in self._data["meals"]:
            raise ValueError("Unknown meal")
        if any(item["round_id"] == result.round_id and item["meal_id"] == result.meal_id for item in self._data["results"]):
            raise ValueError("Duplicate result")
        self._data["results"].append(asdict(result))
        await self.async_save()


def deserialize_user(data: dict[str, Any]) -> User:
    """Rebuild a voter domain object from persisted data."""
    return User(id=data["id"], name=data["name"], active=data["active"])


def deserialize_meal(data: dict[str, Any]) -> Meal:
    """Rebuild a Meal domain object from persisted data."""
    return Meal(id=data["id"], name=data["name"], active=data["active"])


def deserialize_vote(data: dict[str, Any]) -> Vote:
    """Rebuild a Vote domain object from persisted data."""
    return Vote(round_id=data["round_id"], user_id=data["user_id"], meal_id=data["meal_id"])


def deserialize_round(data: dict[str, Any]) -> VotingRound:
    """Rebuild a VotingRound domain object from persisted data."""
    return VotingRound(
        id=data["id"], number=data["number"], created_at=datetime.fromisoformat(data["created_at"]),
        voting_deadline=datetime.fromisoformat(data["voting_deadline"]), meals_required=data["meals_required"],
        voter_ids=tuple(data["voter_ids"]),
        closed_at=datetime.fromisoformat(data["closed_at"]) if data["closed_at"] else None,
        status=VotingRoundStatus(data["status"]),
    )


def deserialize_result(data: dict[str, Any]) -> RoundResult:
    """Rebuild a RoundResult domain object from persisted data."""
    return RoundResult(round_id=data["round_id"], meal_id=data["meal_id"], selected=data["selected"], decision_score=data["decision_score"], vote_score=data["vote_score"], historical_score=data["historical_score"], recency_score=data["recency_score"], rank=data["rank"], explanation=data["explanation"])


def _serialize_round(voting_round: VotingRound) -> dict[str, Any]:
    """Serialise a voting round into JSON-compatible values."""
    data = asdict(voting_round)
    data["created_at"] = voting_round.created_at.isoformat()
    data["voting_deadline"] = voting_round.voting_deadline.isoformat()
    data["closed_at"] = voting_round.closed_at.isoformat() if voting_round.closed_at else None
    data["voter_ids"] = list(voting_round.voter_ids)
    data["status"] = voting_round.status.value
    return data
