"""Tests for the WFD decision engine."""

from datetime import UTC, datetime, timedelta

from .decision_engine import DecisionEngine
from .models import Meal, Vote, VotingRound
from .models.voting_round import VotingRoundStatus


def round_(number: int, round_id: str, meals_required: int = 1, voters: int = 2) -> VotingRound:
    created = datetime(2026, 1, number, tzinfo=UTC)
    return VotingRound(
        id=round_id,
        number=number,
        created_at=created,
        voting_deadline=created + timedelta(days=1),
        meals_required=meals_required,
        voter_ids=tuple(f"voter-{index}" for index in range(voters)),
        closed_at=created + timedelta(hours=2),
        status=VotingRoundStatus.RESULTS_STORED,
    )


def test_current_round_votes_have_priority_over_history() -> None:
    current = round_(3, "current")
    meals = [Meal("a", "Alpha"), Meal("b", "Beta")]
    results = DecisionEngine().decide(
        meals,
        current,
        [Vote("current", "voter-0", "b")],
        [round_(1, "history-1"), round_(2, "history-2")],
        {
            "history-1": [Vote("history-1", "voter-0", "a")],
            "history-2": [Vote("history-2", "voter-0", "a")],
        },
    )

    assert [result.meal_id for result in results] == ["b", "a"]
    assert results[0].vote_score == 0.5
    assert results[1].historical_score == 0.5


def test_historical_score_includes_zero_vote_rounds() -> None:
    current = round_(3, "current")
    meals = [Meal("a", "Alpha")]
    results = DecisionEngine().decide(
        meals,
        current,
        [],
        [round_(1, "history-1"), round_(2, "history-2")],
        {"history-1": [Vote("history-1", "voter-0", "a")], "history-2": []},
    )

    assert results[0].historical_score == 0.25


def test_recency_prefers_recently_chosen_meal_when_other_scores_match() -> None:
    current = round_(4, "current")
    meals = [Meal("a", "Alpha"), Meal("b", "Beta")]
    history = [round_(1, "history-1"), round_(3, "history-3")]
    results = DecisionEngine().decide(
        meals,
        current,
        [],
        history,
        {
            "history-1": [Vote("history-1", "voter-0", "b")],
            "history-3": [Vote("history-3", "voter-0", "a")],
        },
    )

    assert [result.meal_id for result in results] == ["a", "b"]
    assert results[0].recency_score == 1.0
    assert results[1].recency_score == 1 / 3


def test_ties_are_deterministic_and_selection_is_exact() -> None:
    current = round_(2, "current", meals_required=2, voters=1)
    meals = [Meal("z", "Same"), Meal("a", "Same"), Meal("x", "Other")]
    results = DecisionEngine().decide(meals, current, [], [], {})

    assert [result.meal_id for result in results] == ["x", "a", "z"]
    assert sum(result.selected for result in results) == 2
    assert all("Current" in result.explanation for result in results)
