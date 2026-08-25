"""Voting round orchestration for WFD."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from .decision_engine import DecisionEngine
from .models import Vote, VotingRound
from .models.voting_round import VotingRoundStatus
from .storage import WFDStorage
from .updates import async_signal_update
from .voting import validate_selection

try:
    from homeassistant.helpers.event import async_track_point_in_time
except ModuleNotFoundError:
    async_track_point_in_time = None


class VotingError(ValueError):
    """Raised when a voting operation cannot be completed."""


class VotingManager:
    """Coordinate voting rounds without exposing individual votes."""

    def _fire_event(self, event_type: str, data: dict) -> None:
        if self._hass is not None and hasattr(self._hass, "bus"):
            self._hass.bus.async_fire(event_type, data)

    def __init__(
        self,
        storage: WFDStorage,
        meal_library,
        household,
        default_meals_required: int = 1,
        default_deadline_minutes: int = 1440,
        hass=None,
    ) -> None:
        self._storage = storage
        self._meal_library = meal_library
        self._household = household
        self._default_meals_required = default_meals_required
        self._default_deadline_minutes = default_deadline_minutes
        self._hass = hass
        self._decision_engine = DecisionEngine()
        self._deadline_unsub = None

    def _clear_deadline_timer(self) -> None:
        if self._deadline_unsub is not None:
            self._deadline_unsub()
            self._deadline_unsub = None

    def _schedule_deadline_timer(self, round_: VotingRound) -> None:
        self._clear_deadline_timer()
        if async_track_point_in_time is not None and self._hass is not None:
            self._deadline_unsub = async_track_point_in_time(
                self._hass, self._deadline_reached, round_.voting_deadline
            )

    def _deadline_reached(self, _now: datetime) -> None:
        self._hass.async_create_task(self._async_close_due_round())

    async def _async_close_due_round(self) -> None:
        try:
            await self.async_close_round((await self._storage.async_get_voting_rounds())[-1].id)
        except (IndexError, VotingError):
            return
        await async_signal_update(self._hass)

    async def async_stop(self) -> None:
        """Stop scheduled voting callbacks during integration unload."""
        self._clear_deadline_timer()

    async def async_create_round(
        self,
        meals_required: int | None = None,
        deadline_minutes: int | None = None,
    ) -> VotingRound:
        """Create and activate a round using current active meals and voters."""
        meals_required = self._default_meals_required if meals_required is None else meals_required
        deadline_minutes = self._default_deadline_minutes if deadline_minutes is None else deadline_minutes
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
        self._schedule_deadline_timer(round_)
        self._fire_event(
            "wfd_voting_started",
            {
                "round_id": round_.id,
                "meals_required": round_.meals_required,
                "voter_count": round_.voter_count,
                "voting_deadline": round_.voting_deadline.isoformat(),
            },
        )
        return round_

    async def async_get_round(self, round_id: str) -> VotingRound | None:
        """Return a round for service event metadata."""
        return await self._storage.async_get_voting_round(round_id)

    async def async_cancel_round(self, round_id: str, now: datetime | None = None) -> None:
        """Cancel an active round without generating results."""
        round_ = await self._storage.async_get_voting_round(round_id)
        if round_ is None:
            raise VotingError("Unknown voting round")
        if round_.status is not VotingRoundStatus.ACTIVE:
            raise VotingError("Voting round is not active")
        await self._storage.async_delete_voting_round(round_id)
        self._clear_deadline_timer()
        self._fire_event("wfd_voting_cancelled", {"round_id": round_id})

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
        self._clear_deadline_timer()
        decision_round = replace(round_, closed_at=now, status=VotingRoundStatus.DECISION_GENERATED)
        await self._storage.async_set_voting_round(decision_round)
        current_votes = await self._storage.async_get_votes(round_id)
        all_rounds = await self._storage.async_get_voting_rounds()
        completed_rounds = [item for item in all_rounds if item.id != round_id]
        historical_votes = {
            item.id: await self._storage.async_get_votes(item.id)
            for item in completed_rounds
        }
        historical_results = {
            item.id: await self._storage.async_get_results(item.id)
            for item in completed_rounds
        }
        meals = await self._meal_library.async_get_meals(active_only=True)
        results = self._decision_engine.decide(
            meals,
            round_,
            current_votes,
            completed_rounds,
            historical_votes,
            historical_results,
        )
        for result in results:
            await self._storage.async_add_result(result)
        await self._storage.async_mark_round_results_stored(replace(round_, closed_at=now, status=VotingRoundStatus.RESULTS_STORED))
        event_data = {
            "round_id": round_id,
            "selected_meals": [result.meal_id for result in results if result.selected],
            "meals_required": round_.meals_required,
        }
        self._fire_event("wfd_voting_completed", event_data)
        self._fire_event("wfd_results_available", event_data)
        return results

    async def async_get_public_state(self) -> dict:
        """Return progress and completed selections without exposing private votes."""
        rounds = await self._storage.async_get_voting_rounds()
        active = next((item for item in reversed(rounds) if item.status is VotingRoundStatus.ACTIVE), None)
        if active is not None:
            submitted = await self._storage.async_get_submitted_voter_count(active.id)
            if submitted >= active.voter_count or datetime.now(UTC) >= active.voting_deadline:
                await self.async_close_round(active.id)
                return await self.async_get_public_state()
            return {
                "status": active.status.value,
                "round_id": active.id,
                "submitted": submitted,
                "voters": active.voter_count,
                "meals_required": active.meals_required,
                "default_meals_required": self._default_meals_required,
                "default_deadline_minutes": self._default_deadline_minutes,
            }
        latest = rounds[-1] if rounds else None
        if latest is not None and latest.status is VotingRoundStatus.RESULTS_STORED:
            results = await self._storage.async_get_results(latest.id)
            votes = await self._storage.async_get_votes(latest.id)
            vote_counts = Counter(vote.meal_id for vote in votes)
            historical_groups = {}
            for result in results:
                historical_groups.setdefault(result.vote_score, []).append(result)
            public_results = []
            for result in results:
                tie_group = historical_groups[result.vote_score]
                tiebreak_label = None
                tiebreak_score = None
                if len(tie_group) > 1:
                    historical_scores = {item.historical_score for item in tie_group}
                    recency_scores = {item.recency_score for item in tie_group}
                    if len(historical_scores) > 1:
                        tiebreak_label = "Historical score"
                        tiebreak_score = result.historical_score
                    elif len(recency_scores) > 1:
                        tiebreak_label = "Recency score"
                        tiebreak_score = result.recency_score
                public_results.append({
                    "meal_id": result.meal_id,
                    "selected": result.selected,
                    "rank": result.rank,
                    "votes_received": vote_counts[result.meal_id],
                    "voter_count": latest.voter_count,
                    "vote_score": result.vote_score,
                    "historical_score": result.historical_score,
                    "recency_score": result.recency_score,
                    "decision_score": result.decision_score,
                    "tiebreak_label": tiebreak_label,
                    "tiebreak_score": tiebreak_score,
                    "explanation": result.explanation,
                })
            return {
                "status": latest.status.value,
                "round_id": latest.id,
                "selected_meals": [result.meal_id for result in results if result.selected],
                "results": public_results,
                "meals_required": latest.meals_required,
                "default_meals_required": self._default_meals_required,
                "default_deadline_minutes": self._default_deadline_minutes,
            }
        return {
            "status": "idle",
            "round_id": None,
            "submitted": 0,
            "voters": 0,
            "meals_required": 0,
            "default_meals_required": self._default_meals_required,
            "default_deadline_minutes": self._default_deadline_minutes,
        }
