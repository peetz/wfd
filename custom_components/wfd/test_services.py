"""Tests for WFD Home Assistant services."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest

from .models import RoundResult, VotingRound
from .models.voting_round import VotingRoundStatus
from .services import async_setup_services


@pytest.mark.asyncio
async def test_registers_meal_services():
    hass = Mock()
    hass.services.async_register = Mock()
    library = Mock()

    await async_setup_services(hass, library)

    assert hass.services.async_register.call_count == 4


@pytest.mark.asyncio
async def test_add_meal_calls_library():
    hass = Mock()
    registrations = {}

    def register(domain, service, handler):
        registrations[service] = handler

    hass.services.async_register = register
    library = Mock()
    library.async_add_meal = AsyncMock()

    await async_setup_services(hass, library)
    await registrations["add_meal"](Mock(data={"name": "Pizza"}))

    library.async_add_meal.assert_awaited_once_with("Pizza")


@pytest.mark.asyncio
async def test_start_voting_fires_privacy_safe_event_with_configured_defaults():
    hass = Mock()
    registrations = {}
    hass.services.async_register = lambda domain, service, handler: registrations.setdefault(service, handler)
    hass.bus.async_fire = Mock()
    library = Mock()
    household = Mock()
    household.async_is_admin_user = AsyncMock(return_value=True)
    created = datetime.now(UTC)
    round_ = VotingRound(
        id="round-1",
        number=1,
        created_at=created,
        voting_deadline=created + timedelta(minutes=30),
        meals_required=2,
        voter_ids=("voter-1", "voter-2"),
        status=VotingRoundStatus.ACTIVE,
    )
    voting = Mock()
    voting.async_create_round = AsyncMock(return_value=round_)

    await async_setup_services(hass, library, household, voting)
    await registrations["start_voting"](Mock(data={}, context=Mock(user_id="admin")))

    voting.async_create_round.assert_awaited_once_with(None, None)
    hass.bus.async_fire.assert_called_once_with(
        "wfd_voting_started",
        {
            "round_id": "round-1",
            "meals_required": 2,
            "voter_count": 2,
            "voting_deadline": round_.voting_deadline.isoformat(),
        },
    )


@pytest.mark.asyncio
async def test_close_voting_fires_completion_and_results_events():
    hass = Mock()
    registrations = {}
    hass.services.async_register = lambda domain, service, handler: registrations.setdefault(service, handler)
    hass.bus.async_fire = Mock()
    library = Mock()
    household = Mock()
    household.async_is_admin_user = AsyncMock(return_value=True)
    created = datetime.now(UTC)
    round_ = VotingRound(
        id="round-1",
        number=1,
        created_at=created,
        voting_deadline=created,
        meals_required=1,
        voter_ids=("voter-1",),
        closed_at=created,
        status=VotingRoundStatus.RESULTS_STORED,
    )
    result = RoundResult("round-1", "meal-1", True, 1.0, 1.0, 0.0, 0.0, 1, "selected")
    voting = Mock()
    voting.async_close_round = AsyncMock(return_value=[result])
    voting.async_get_round = AsyncMock(return_value=round_)

    await async_setup_services(hass, library, household, voting)
    await registrations["close_voting"](Mock(data={"round_id": "round-1"}, context=Mock(user_id="admin")))

    assert [call.args[0] for call in hass.bus.async_fire.call_args_list] == [
        "wfd_voting_completed",
        "wfd_results_available",
    ]
