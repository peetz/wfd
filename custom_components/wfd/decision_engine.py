"""Deterministic, explainable meal decision engine."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from .models import Meal, RoundResult, Vote, VotingRound
from .models.voting_round import VotingRoundStatus


@dataclass(frozen=True, slots=True)
class MealScore:
    """Comparable score components for one meal."""

    meal: Meal
    vote_score: float
    historical_score: float
    recency_score: float

    @property
    def decision_score(self) -> float:
        """Return a readable aggregate without replacing priority ordering."""
        return self.vote_score + self.historical_score + self.recency_score

    @property
    def sort_key(self) -> tuple[float, float, float, str, str]:
        """Return the priority-ordered, deterministic ranking key."""
        return (
            -self.vote_score,
            -self.historical_score,
            -self.recency_score,
            self.meal.name.casefold(),
            self.meal.id,
        )


class DecisionEngine:
    """Rank meals from current votes, history, recency, and stable ties."""

    def decide(
        self,
        meals: Iterable[Meal],
        current_round: VotingRound,
        current_votes: Iterable[Vote],
        completed_rounds: Iterable[VotingRound],
        historical_votes: Mapping[str, Iterable[Vote]],
        historical_results: Mapping[str, Iterable[RoundResult]] | None = None,
    ) -> list[RoundResult]:
        """Return one ranked result for every active meal.

        Priority is strict: current-round support, historical support, then
        recency. Historical averages include completed rounds with zero votes.
        """
        active_meals = [meal for meal in meals if meal.active]
        current_votes = list(current_votes)
        historical_results = historical_results or {}
        completed_rounds = [
            round_
            for round_ in completed_rounds
            if round_.id != current_round.id
            and round_.status
            in {
                VotingRoundStatus.CLOSED,
                VotingRoundStatus.DECISION_GENERATED,
                VotingRoundStatus.RESULTS_STORED,
            }
        ]
        current_counts = {meal.id: 0 for meal in active_meals}
        for vote in current_votes:
            if vote.meal_id in current_counts:
                current_counts[vote.meal_id] += 1

        history_counts = {meal.id: [] for meal in active_meals}
        last_chosen_round: dict[str, int] = {}
        for round_ in completed_rounds:
            counts = {meal.id: 0 for meal in active_meals}
            for vote in historical_votes.get(round_.id, ()):
                if vote.meal_id in counts:
                    counts[vote.meal_id] += 1
            for meal_id, count in counts.items():
                history_counts[meal_id].append(
                    count / round_.voter_count if round_.voter_count else 0.0
                )
            for result in historical_results.get(round_.id, ()):
                if result.selected:
                    last_chosen_round[result.meal_id] = max(
                        last_chosen_round.get(result.meal_id, 0), round_.number
                    )

        scores = []
        for meal in active_meals:
            history = history_counts[meal.id]
            last_round = last_chosen_round.get(meal.id)
            scores.append(
                MealScore(
                    meal=meal,
                    vote_score=current_counts[meal.id] / current_round.voter_count
                    if current_round.voter_count
                    else 0.0,
                    historical_score=sum(history) / len(history) if history else 0.0,
                    recency_score=(
                        1 / (current_round.number - last_round)
                        if last_round is not None
                        and current_round.number > last_round
                        else 0.0
                    ),
                )
            )

        ranked = sorted(scores, key=lambda score: score.sort_key)
        results = []
        for rank, score in enumerate(ranked, 1):
            results.append(
                RoundResult(
                    round_id=current_round.id,
                    meal_id=score.meal.id,
                    selected=rank <= current_round.meals_required,
                    decision_score=score.decision_score,
                    vote_score=score.vote_score,
                    historical_score=score.historical_score,
                    recency_score=score.recency_score,
                    rank=rank,
                    explanation=(
                        f"Current {score.vote_score:.3f}; historical "
                        f"{score.historical_score:.3f}; recency "
                        f"{score.recency_score:.3f}; tie-break "
                        f"{score.meal.name} ({score.meal.id})"
                    ),
                )
            )
        return results
