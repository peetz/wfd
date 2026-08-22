"""Tests for WFD persistent storage."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from .models import Meal, RoundResult, User, Vote, VotingRound
from .models.voting_round import VotingRoundStatus
from .storage import (
    WFDStorage,
    deserialize_meal,
    deserialize_result,
    deserialize_round,
    deserialize_user,
    deserialize_vote,
)


@pytest.fixture
def storage() -> WFDStorage:
    """Return a WFD storage instance with an isolated mocked HA store."""
    storage = object.__new__(WFDStorage)
    storage._store = MagicMock()
    storage._store.async_load = AsyncMock(return_value=None)
    storage._store.async_save = AsyncMock()
    storage._data = storage._empty_data()
    return storage


def active_round() -> VotingRound:
    """Return a minimal active round for storage tests."""
    created = datetime.now(UTC)
    return VotingRound(
        id="round-1",
        number=1,
        created_at=created,
        voting_deadline=created + timedelta(days=1),
        meals_required=1,
        voter_ids=("user-1",),
        status=VotingRoundStatus.ACTIVE,
    )


@pytest.mark.asyncio
async def test_load_initialises_empty_store(storage: WFDStorage) -> None:
    """A new installation starts with empty collections."""
    await storage.async_load()

    assert storage._data == storage._empty_data()
    storage._store.async_load.assert_awaited_once()


@pytest.mark.asyncio
async def test_user_and_meal_are_persisted(storage: WFDStorage) -> None:
    """Users and meals are stored by stable ID."""
    await storage.async_set_user(User(id="user-1", name="Steve"))
    await storage.async_set_meal(Meal(id="meal-1", name="Pizza"))

    assert storage._data["users"]["user-1"]["name"] == "Steve"
    assert storage._data["meals"]["meal-1"]["name"] == "Pizza"
    assert storage._store.async_save.await_count == 2


@pytest.mark.asyncio
async def test_vote_validates_relationships_and_rejects_duplicate(storage: WFDStorage) -> None:
    """Votes require valid active round, voter, and meal references."""
    await storage.async_set_user(User(id="user-1", name="Steve"))
    await storage.async_set_meal(Meal(id="meal-1", name="Pizza"))
    await storage.async_set_voting_round(active_round())

    vote = Vote(round_id="round-1", user_id="user-1", meal_id="meal-1")
    await storage.async_add_vote(vote)

    with pytest.raises(ValueError, match="Duplicate vote"):
        await storage.async_add_vote(vote)


@pytest.mark.asyncio
async def test_invalid_vote_reference_is_rejected(storage: WFDStorage) -> None:
    """Votes cannot reference unknown users or meals."""
    await storage.async_set_voting_round(active_round())

    with pytest.raises(ValueError, match="Unknown user"):
        await storage.async_add_vote(
            Vote(round_id="round-1", user_id="user-1", meal_id="meal-1")
        )


@pytest.mark.asyncio
async def test_completed_round_rejects_votes_and_updates(storage: WFDStorage) -> None:
    """Completed rounds cannot be changed through the storage layer."""
    await storage.async_set_user(User(id="user-1", name="Steve"))
    await storage.async_set_meal(Meal(id="meal-1", name="Pizza"))

    round_ = active_round()
    await storage.async_set_voting_round(round_)

    completed = VotingRound(
        id=round_.id,
        number=round_.number,
        created_at=round_.created_at,
        voting_deadline=round_.voting_deadline,
        meals_required=round_.meals_required,
        voter_ids=round_.voter_ids,
        closed_at=round_.created_at,
        status=VotingRoundStatus.RESULTS_STORED,
    )
    storage._data["rounds"][round_.id] = {
        **storage._data["rounds"][round_.id],
        "status": VotingRoundStatus.RESULTS_STORED.value,
        "closed_at": completed.closed_at.isoformat(),
    }

    with pytest.raises(ValueError, match="immutable"):
        await storage.async_set_voting_round(completed)

    with pytest.raises(ValueError, match="active rounds"):
        await storage.async_add_vote(
            Vote(round_id="round-1", user_id="user-1", meal_id="meal-1")
        )


@pytest.mark.asyncio
async def test_result_requires_decision_generated_round(storage: WFDStorage) -> None:
    """Results can only be written after decision generation."""
    await storage.async_set_meal(Meal(id="meal-1", name="Pizza"))
    await storage.async_set_voting_round(active_round())

    result = RoundResult(
        round_id="round-1",
        meal_id="meal-1",
        selected=True,
        decision_score=0.9,
        vote_score=1.0,
        historical_score=0.8,
        recency_score=0.2,
        rank=1,
        explanation="Selected.",
    )

    with pytest.raises(ValueError, match="decision generation"):
        await storage.async_add_result(result)


@pytest.mark.asyncio
async def test_round_serialization_round_trips(storage: WFDStorage) -> None:
    """A stored round can be reconstructed as the same domain model."""
    round_ = active_round()
    await storage.async_set_voting_round(round_)

    restored = deserialize_round(storage._data["rounds"][round_.id])

    assert restored == round_


def test_all_domain_models_deserialize() -> None:
    """Persisted model dictionaries reconstruct the original domain objects."""
    user = User(id="user-1", name="Steve", active=False)
    meal = Meal(id="meal-1", name="Pizza", active=False)
    vote = Vote(round_id="round-1", user_id="user-1", meal_id="meal-1")
    round_ = active_round()
    result = RoundResult(
        round_id="round-1",
        meal_id="meal-1",
        selected=True,
        decision_score=0.9,
        vote_score=1.0,
        historical_score=0.8,
        recency_score=0.2,
        rank=1,
        explanation="Selected.",
    )

    assert deserialize_user({"id": user.id, "name": user.name, "active": user.active}) == user
    assert deserialize_meal({"id": meal.id, "name": meal.name, "active": meal.active}) == meal
    assert deserialize_vote({"round_id": vote.round_id, "user_id": vote.user_id, "meal_id": vote.meal_id}) == vote
    assert deserialize_round(
        {
            **storage_round_data(round_),
        }
    ) == round_
    assert deserialize_result({
        "round_id": result.round_id,
        "meal_id": result.meal_id,
        "selected": result.selected,
        "decision_score": result.decision_score,
        "vote_score": result.vote_score,
        "historical_score": result.historical_score,
        "recency_score": result.recency_score,
        "rank": result.rank,
        "explanation": result.explanation,
    }) == result


def storage_round_data(round_: VotingRound) -> dict[str, object]:
    """Return JSON-compatible round data matching the storage format."""
    return {
        "id": round_.id,
        "number": round_.number,
        "created_at": round_.created_at.isoformat(),
        "voting_deadline": round_.voting_deadline.isoformat(),
        "meals_required": round_.meals_required,
        "voter_ids": list(round_.voter_ids),
        "closed_at": None,
        "status": round_.status.value,
    }
