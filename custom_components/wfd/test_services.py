"""Tests for WFD Home Assistant services."""

from unittest.mock import AsyncMock, Mock

import pytest

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
