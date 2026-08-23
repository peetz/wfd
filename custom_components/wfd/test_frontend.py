"""Tests for WFD frontend registration."""

from custom_components.wfd.frontend import (
    PANEL_ICON,
    PANEL_TITLE,
    PANEL_URL,
)


def test_frontend_panel_metadata():
    """Panel metadata is defined."""
    assert PANEL_TITLE == "What's For Dinner"
    assert PANEL_URL == "wfd"
    assert PANEL_ICON == "mdi:silverware-fork-knife"
