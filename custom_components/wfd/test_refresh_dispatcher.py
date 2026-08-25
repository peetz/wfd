"""Tests for WFD refresh signalling."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from custom_components.wfd.sensor import WFDBaseSensor
from custom_components.wfd.updates import SIGNAL_WFD_UPDATED, async_signal_update


def test_refresh_signal_constant_exists():
    """Refresh signal should have a stable identifier."""
    assert SIGNAL_WFD_UPDATED == "wfd_updated"


def test_async_signal_update_is_callable_without_home_assistant():
    """The refresh helper should remain importable in unit tests."""
    async_signal_update(None)


@pytest.mark.asyncio
async def test_sensor_signal_refreshes_and_writes_state_immediately():
    """A dispatcher signal publishes fresh sensor data without polling."""
    hass = MagicMock()
    hass.async_create_task.side_effect = asyncio.create_task
    sensor = WFDBaseSensor(hass)
    sensor.async_update = AsyncMock()
    sensor.async_write_ha_state = Mock()

    sensor._refresh()
    await asyncio.sleep(0)

    sensor.async_update.assert_awaited_once()
    sensor.async_write_ha_state.assert_called_once_with()
