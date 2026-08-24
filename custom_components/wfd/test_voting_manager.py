"""Tests for the voting round workflow."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from .models import Meal, User, Vote, VotingRound
from .models.voting_round import VotingRoundStatus
from .voting_manager import VotingManager, VotingError


@pytest.fixture
def manager():
    storage = MagicMock()
    storage.async_get_voting_rounds = AsyncMock()
    storage.async_get_votes = AsyncMock(return_value=[])
    storage.async_set_voting_round = AsyncMock()
    storage.async_get_voting_round = AsyncMock()
    storage.async_has_votes = AsyncMock()
    storage.async_add_vote = AsyncMock()
    storage.async_get_votes = AsyncMock()
    storage.async_get_submitted_voter_count = AsyncMock()
    storage.async_mark_round_results_stored = AsyncMock()
    storage.async_add_result = AsyncMock()
    meal_library = MagicMock()
    meal_library.async_get_meals = AsyncMock()
    household = MagicMock()
    household.async_get_voters = AsyncMock()
    return VotingManager(storage, meal_library, household), storage, meal_library, household


@pytest.mark.asyncio
async def test_create_round_captures_current_meals_and_voters(manager):
    voting, storage, meals, household = manager
    meals.async_get_meals.return_value = [Meal("m1", "Pizza"), Meal("m2", "Pasta")]
    household.async_get_voters.return_value = [User("u1", "Alex"), User("u2", "Sam")]
    storage.async_get_voting_rounds.return_value = []
    round_ = await voting.async_create_round(2, 30)
    assert round_.status is VotingRoundStatus.ACTIVE
    assert round_.voter_ids == ("u1", "u2")
    storage.async_set_voting_round.assert_awaited_once_with(round_)


@pytest.mark.asyncio
async def test_vote_is_private_immutable_and_validated(manager):
    voting, storage, meals, _ = manager
    round_ = MagicMock(meals_required=2, voter_ids=("u1",), status=VotingRoundStatus.ACTIVE)
    storage.async_get_voting_round.return_value = round_
    storage.async_has_votes.return_value = False
    meals.async_get_meals.return_value = [Meal("m1", "Pizza"), Meal("m2", "Pasta")]
    await voting.async_submit_vote("r1", "u1", ["m1", "m2"])
    assert storage.async_add_vote.await_count == 2
    storage.async_has_votes.return_value = True
    with pytest.raises(VotingError, match="changed"):
        await voting.async_submit_vote("r1", "u1", ["m1", "m2"])


@pytest.mark.asyncio
async def test_public_state_exposes_only_selected_meals_after_completion(manager):
    voting, storage, _, _ = manager
    completed = MagicMock(status=VotingRoundStatus.RESULTS_STORED, id="round-1", meals_required=1)
    storage.async_get_voting_rounds.return_value = [completed]
    storage.async_get_results = AsyncMock(return_value=[
        MagicMock(
            meal_id="meal-1",
            selected=True,
            rank=1,
            vote_score=1.0,
            historical_score=0.5,
            recency_score=0.0,
            decision_score=1.5,
            explanation="Selected.",
        ),
        MagicMock(
            meal_id="meal-2",
            selected=False,
            rank=2,
            vote_score=0.0,
            historical_score=0.0,
            recency_score=0.0,
            decision_score=0.0,
            explanation="Not selected.",
        ),
    ])

    state = await voting.async_get_public_state()

    assert state["status"] == "results_stored"
    assert state["selected_meals"] == ["meal-1"]
    assert state["results"][0]["votes_received"] == 0
    assert state["results"][0]["voter_count"] == completed.voter_count

@pytest.mark.asyncio
async def test_close_round_uses_decision_engine_and_persists_all_results(manager):
    voting, storage, meals, household = manager
    created = datetime.now(UTC)
    current = VotingRound(
        id="current",
        number=2,
        created_at=created,
        voting_deadline=created + timedelta(minutes=10),
        meals_required=1,
        voter_ids=("u1", "u2"),
        status=VotingRoundStatus.ACTIVE,
    )
    previous = VotingRound(
        id="previous",
        number=1,
        created_at=created - timedelta(days=1),
        voting_deadline=created,
        meals_required=1,
        voter_ids=("u1", "u2"),
        closed_at=created,
        status=VotingRoundStatus.RESULTS_STORED,
    )
    storage.async_get_voting_round.return_value = current
    storage.async_get_submitted_voter_count.return_value = 2
    storage.async_get_votes.side_effect = [
        [Vote("current", "u1", "meal-2")],
        [Vote("previous", "u1", "meal-1")],
    ]
    storage.async_get_voting_rounds.return_value = [previous, current]
    meals.async_get_meals.return_value = [
        Meal("meal-1", "Pizza"),
        Meal("meal-2", "Pasta"),
    ]

    results = await voting.async_close_round("current", now=created)

    assert [result.meal_id for result in results] == ["meal-2", "meal-1"]
    assert storage.async_add_result.await_count == 2
    storage.async_mark_round_results_stored.assert_awaited_once()
