"""Voting round orchestration for WFD."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from .models import RoundResult, Vote, VotingRound
from .models.voting_round import VotingRoundStatus
from .storage import WFDStorage
from .voting import validate_selection


class VotingError(ValueError):
    """Raised when a voting operation cannot be completed."""


class VotingManager:
    """Coordinate voting rounds without exposing individual votes."""

    def __init__(self, storage: WFDStorage, meal_library, household) -> None:
        self._storage = storage
        self._meal_library = meal_library
        self._household = household

    async def async_create_round(self, meals_required: int, deadline_minutes: int = 1440) -> VotingRound:
        """Create and activate a round using current active meals and voters."""
        meals = await self._meal_library.async_get_meals(active_only=True)
        voters = await self._household.async_get_voters(active_only=True)
        if meals_required < 1 or meals_required > len(meals):
            raise VotingError("The number of meals must be between 1 and the active meal count")
        if not voters:
            raise VotingError("At least one active voter is required")
        existing = await self._storage.async_get_voting_rounds()
        now = datetime.now(UTC)
        round_ = VotingRound(str(uuid4()), len(existing) + 1, now, now + timedelta(minutes=deadline_minutes), meals_required, tuple(voter.id for voter in voters), status=VotingRoundStatus.ACTIVE)
        await self._storage.async_set_voting_round(round_)
        return round_

    async def async_submit_vote(self, round_id: str, user_id: str, meal_ids: list[str]) -> None:
        """Validate and persist one voter's private selections."""
        round_ = await self._storage.async_get_voting_round(round_id)
        if round_ is None:
            raise VotingError("Unknown voting round")
        if round_.status is not VotingRoundStatus.ACTIVE:
            raise VotingError("Voting round is not active")
        if user_id not in round_.voter_ids:
            raise VotingError("User is not a voter in this round")
        if await self._storage.async_has_votes(round_id, user_id):
            raise VotingError("Votes cannot be changed")
        validate_selection(meal_ids, round_.meals_required)
        active_ids = {meal.id for meal in await self._meal_library.async_get_meals(active_only=True)}
        if any(meal_id not in active_ids for meal_id in meal_ids):
            raise VotingError("Votes must reference active meals")
        for meal_id in meal_ids:
            await self._storage.async_add_vote(Vote(round_id, user_id, meal_id))

    async def async_close_round(self, round_id: str, now: datetime | None = None) -> list[RoundResult]:
        """Close a round and persist deterministic results."""
        round_ = await self._storage.async_get_voting_round(round_id)
        if round_ is None:
            raise VotingError("Unknown voting round")
        if round_.status is not VotingRoundStatus.ACTIVE:
            raise VotingError("Voting round is already closed")
        now = now or datetime.now(UTC)
        if await self._storage.async_get_submitted_voter_count(round_id) < round_.voter_count and now < round_.voting_deadline:
            raise VotingError("Not all voters have submitted")
        decision_round = replace(round_, closed_at=now, status=VotingRoundStatus.DECISION_GENERATED)
        await self._storage.async_set_voting_round(decision_round)
        scores = Counter(vote.meal_id for vote in await self._storage.async_get_votes(round_id))
        meals = await self._meal_library.async_get_meals(active_only=True)
        ranked = sorted(meals, key=lambda meal: (-scores[meal.id], meal.name.casefold(), meal.id))
        results = []
        for rank, meal in enumerate(ranked, 1):
            score = float(scores[meal.id])
            result = RoundResult(round_id, meal.id, rank <= round_.meals_required, score, score, 0.0, 0.0, rank, f"{score:g} private votes")
            await self._storage.async_add_result(result)
            results.append(result)
        await self._storage.async_mark_round_results_stored(replace(round_, closed_at=now, status=VotingRoundStatus.RESULTS_STORED))
        return results

    async def async_get_public_state(self) -> dict:
        """Return progress and completed selections without exposing private votes."""
        rounds = await self._storage.async_get_voting_rounds()
        active = next((item for item in reversed(rounds) if item.status is VotingRoundStatus.ACTIVE), None)
        if active is not None:
            return {
                "status": active.status.value,
                "round_id": active.id,
                "submitted": await self._storage.async_get_submitted_voter_count(active.id),
                "voters": active.voter_count,
                "meals_required": active.meals_required,
            }
        latest = rounds[-1] if rounds else None
        if latest is not None and latest.status is VotingRoundStatus.RESULTS_STORED:
            results = await self._storage.async_get_results(latest.id)
            return {
                "status": latest.status.value,
                "round_id": latest.id,
                "selected_meals": [result.meal_id for result in results if result.selected],
                "meals_required": latest.meals_required,
            }
        return {"status": "idle", "round_id": None, "submitted": 0, "voters": 0, "meals_required": 0}
