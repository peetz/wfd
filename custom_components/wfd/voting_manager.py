"""Voting round orchestration for WFD."""

from __future__ import annotations

from collections import Counter
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
        round_ = VotingRound(
            id=str(uuid4()),
            number=len(existing) + 1,
            created_at=now,
            voting_deadline=now + timedelta(minutes=deadline_minutes),
            meals_required=meals_required,
            voter_ids=tuple(voter.id for voter in voters),
            status=VotingRoundStatus.ACTIVE,
        )
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
        voter_count = len(round_.voter_ids)
        submitted = await self._storage.async_get_submitted_voter_count(round_id)
        if submitted < voter_count and now < round_.voting_deadline:
            raise VotingError("Not all voters have submitted")
        closed = round_.__class__(**{**round_.__dict__, "closed_at": now, "status": VotingRoundStatus.DECISION_GENERATED})
        await self._storage.async_set_voting_round(closed)
        votes = await self._storage.async_get_votes(round_id)
        scores = Counter(vote.meal_id for vote in votes)
        meals = await self._meal_library.async_get_meals(active_only=True)
        ranked = sorted(meals, key=lambda meal: (-scores[meal.id], meal.name.casefold(), meal.id))
        results = []
        for rank, meal in enumerate(ranked, 1):
            score = float(scores[meal.id])
            results.append(RoundResult(round_id, meal.id, rank <= round_.meals_required, score, score, 0.0, 0.0, rank, f"{score:g} private votes"))
            await self._storage.async_add_result(results[-1])
        final = round_.__class__(**{**round_.__dict__, "closed_at": now, "status": VotingRoundStatus.RESULTS_STORED})
        await self._storage.async_mark_round_results_stored(final)
        return results

    async def async_get_public_state(self) -> dict:
        """Return progress without revealing individual votes."""
        rounds = await self._storage.async_get_voting_rounds()
        active = next((round_ for round_ in reversed(rounds) if round_.status is VotingRoundStatus.ACTIVE), None)
        if active is None:
            return {"status": "idle", "round_id": None, "submitted": 0, "voters": 0, "meals_required": 0}
        return {"status": active.status.value, "round_id": active.id, "submitted": await self._storage.async_get_submitted_voter_count(active.id), "voters": active.voter_count, "meals_required": active.meals_required}
