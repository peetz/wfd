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

def test_frontend_registration_is_idempotent():
    """Reloading WFD does not attempt to overwrite the sidebar panel."""
    content = open("custom_components/wfd/frontend.py").read()
    assert 'wfd_data.get("_frontend_registered")' in content
    assert 'wfd_data["_frontend_registered"] = True' in content
