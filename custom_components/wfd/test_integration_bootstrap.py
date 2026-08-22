"""Tests for WFD Home Assistant bootstrap."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from . import async_setup_entry, async_unload_entry


@pytest.mark.asyncio
async def test_setup_entry_registers_wfd_runtime():
    """Setup creates runtime objects."""
    hass = MagicMock()
    hass.data = {}
    hass.config_entries = MagicMock()
    entry = MagicMock()
    entry.entry_id = "test"

    await async_setup_entry(hass, entry)

    assert "wfd" in hass.data
    assert "storage" in hass.data["wfd"]["test"]
    assert "meal_library" in hass.data["wfd"]["test"]


@pytest.mark.asyncio
async def test_unload_entry_removes_runtime():
    """Unload removes runtime objects."""
    hass = MagicMock()
    hass.data = {"wfd": {"test": {}}}
    entry = MagicMock()
    entry.entry_id = "test"

    assert await async_unload_entry(hass, entry) is True
    assert "test" not in hass.data["wfd"]
