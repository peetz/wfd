"""Tests for WFD domain models."""

from datetime import UTC, datetime, timedelta

from .meal import Meal
from .round_result import RoundResult
from .user import User
from .vote import Vote
from .voting_round import VotingRound, VotingRoundStatus


def test_meal_and_user_defaults() -> None:
    meal = Meal(id="meal-1", name="Pizza")
    user = User(id="user-1", name="Steve")

    assert meal.active is True
    assert user.active is True


def test_voting_round_retains_participants_and_count() -> None:
    created = datetime.now(UTC)
    round_ = VotingRound(
        id="round-1",
        number=1,
        created_at=created,
        voting_deadline=created + timedelta(days=3),
        meals_required=7,
        voter_ids=("user-1", "user-2", "user-3"),
        status=VotingRoundStatus.ACTIVE,
    )

    assert round_.voter_count == 3
    assert round_.voter_ids == ("user-1", "user-2", "user-3")
    assert round_.status is VotingRoundStatus.ACTIVE


def test_round_result_exposes_selection_status() -> None:
    result = RoundResult(
        round_id="round-1",
        meal_id="meal-1",
        selected=True,
        decision_score=0.91,
        vote_score=1.0,
        historical_score=0.72,
        recency_score=0.2,
        rank=1,
        explanation="Strong vote support.",
    )

    assert result.selection_status == "selected"


def test_vote_identifies_round_user_and_meal() -> None:
    vote = Vote(round_id="round-1", user_id="user-1", meal_id="meal-1")

    assert (vote.round_id, vote.user_id, vote.meal_id) == (
        "round-1",
        "user-1",
        "meal-1",
    )
