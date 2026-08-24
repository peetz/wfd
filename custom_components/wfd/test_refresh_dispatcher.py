"""Tests for WFD refresh signalling."""

from custom_components.wfd.updates import SIGNAL_WFD_UPDATED, async_signal_update


def test_refresh_signal_constant_exists():
    """Refresh signal should have a stable identifier."""
    assert SIGNAL_WFD_UPDATED == "wfd_updated"


def test_async_signal_update_is_callable_without_home_assistant():
    """The refresh helper should remain importable in unit tests."""
    async_signal_update(None)
