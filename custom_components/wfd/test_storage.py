"""Tests for WFD persistent storage."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from .models import Meal, User, Vote, VotingRound
from .models.voting_round import VotingRoundStatus
from .storage import WFDStorage


@pytest.fixture
def storage() -> WFDStorage:
    """Return a WFD storage instance with an isolated mocked HA store."""
    storage = object.__new__(WFDStorage)
    storage._store = MagicMock()
    storage._store.async_load = AsyncMock(return_value=None)
    storage._store.async_save = AsyncMock()
    storage._data = storage._empty_data()
    return storage


@pytest.mark.asyncio
async def test_load_initialises_empty_store(storage: WFDStorage) -> None:
    """A new installation starts with empty collections."""
    await storage.async_load()

    assert storage._data == storage._empty_data()


@pytest.mark.asyncio
async def test_user_and_meal_are_persisted(storage: WFDStorage) -> None:
    """Users and meals are stored by stable ID."""
    await storage.async_set_user(User(id="user-1", name="Steve"))
    await storage.async_set_meal(Meal(id="meal-1", name="Pizza"))

    assert storage._data["users"]["user-1"]["name"] == "Steve"
    assert storage._data["meals"]["meal-1"]["name"] == "Pizza"
    assert storage._store.async_save.await_count == 2


@pytest.mark.asyncio
async def test_duplicate_vote_is_rejected(storage: WFDStorage) -> None:
    """The same user cannot cast the same meal vote twice in a round."""
    vote = Vote(round_id="round-1", user_id="user-1", meal_id="meal-1")
    await storage.async_add_vote(vote)

    with pytest.raises(ValueError, match="Duplicate vote"):
        await storage.async_add_vote(vote)


@pytest.mark.asyncio
async def test_completed_round_is_immutable(storage: WFDStorage) -> None:
    """Completed rounds cannot be overwritten through the storage layer."""
    created = datetime.now(UTC)
    round_ = VotingRound(
        id="round-1",
        number=1,
        created_at=created,
        voting_deadline=created + timedelta(days=1),
        meals_required=1,
        voter_ids=("user-1",),
        closed_at=created,
        status=VotingRoundStatus.CLOSED,
    )
    storage._data["rounds"][round_.id] = {
        "status": VotingRoundStatus.CLOSED,
    }

    with pytest.raises(ValueError, match="immutable"):
        await storage.async_set_voting_round(round_)
