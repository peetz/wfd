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
    assert not hass.bus.async_fire.called


@pytest.mark.asyncio
async def test_cancel_voting_is_admin_only_and_calls_manager():
    hass = Mock()
    registrations = {}
    hass.services.async_register = lambda domain, service, handler: registrations.setdefault(service, handler)
    library = Mock()
    household = Mock()
    household.async_is_admin_user = AsyncMock(return_value=True)
    voting = Mock()
    voting.async_cancel_round = AsyncMock()

    await async_setup_services(hass, library, household, voting)
    await registrations["cancel_voting"](
        Mock(data={"round_id": "round-1"}, context=Mock(user_id="admin"))
    )

    voting.async_cancel_round.assert_awaited_once_with("round-1")
    assert "close_voting" not in registrations
