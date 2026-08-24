"""Tests for the voting round workflow."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from .models import Meal, User
from .voting_manager import VotingError, VotingManager


@pytest.fixture
def manager():
    storage = MagicMock()
    meal_library = MagicMock()
    household = MagicMock()
    manager = VotingManager(storage, meal_library, household)
    return manager, storage, meal_library, household


@pytest.mark.asyncio
async def test_create_round_captures_current_meals_and_voters(manager):
    manager, storage, meals, household = manager
    meals.async_get_meals.return_value = [Meal("m1", "Pizza"), Meal("m2", "Pasta")]
    household.async_get_voters.return_value = [User("u1", "Alex"), User("u2", "Sam")]
    storage.async_get_voting_rounds.return_value = []
    round_ = await manager.async_create_round(2, 30)
    assert round_.status.value == "active"
    assert round_.voter_ids == ("u1", "u2")
    storage.async_set_voting_round.assert_awaited_once_with(round_)


@pytest.mark.asyncio
async def test_vote_is_private_immutable_and_validated(manager):
    manager, storage, meals, household = manager
    now = datetime.now(UTC)
    round_ = MagicMock(meals_required=2, voter_ids=("u1",), status=__import__("custom_components.wfd.models.voting_round", fromlist=["VotingRoundStatus"]).VotingRoundStatus.ACTIVE)
    storage.async_get_voting_round.return_value = round_
    storage.async_has_votes.return_value = False
    meals.async_get_meals.return_value = [Meal("m1", "Pizza"), Meal("m2", "Pasta")]
    await manager.async_submit_vote("r1", "u1", ["m1", "m2"])
    assert storage.async_add_vote.await_count == 2
    storage.async_has_votes.return_value = True
    with pytest.raises(VotingError, match="changed"):
        await manager.async_submit_vote("r1", "u1", ["m1", "m2"])
