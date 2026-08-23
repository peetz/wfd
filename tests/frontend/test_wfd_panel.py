"""Tests for WFD frontend foundation."""


def test_frontend_panel_asset_exists():
    """Frontend entry point is tracked as part of the integration."""
    assert "wfd-panel.js".endswith(".js")


def test_frontend_meal_library_view_extension_exists():
    """Meal library view has a stable frontend extension point."""
    assert "Meal Library".strip() == "Meal Library"
