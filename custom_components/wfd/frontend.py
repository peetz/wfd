"""Frontend registration helpers for WFD."""

from __future__ import annotations

from pathlib import Path


FRONTEND_PATH = "/wfd/frontend"
PANEL_URL = "wfd"
PANEL_TITLE = "What's For Dinner"
PANEL_ICON = "mdi:silverware-fork-knife"


def async_register_frontend(hass) -> None:
    """Register the WFD sidebar panel.

    The panel intentionally contains no business logic. It is a presentation
    layer over WFD entities and services.
    """
    frontend_file = Path(__file__).parent / "frontend" / "wfd-panel.js"

    hass.http.register_static_path(
        FRONTEND_PATH,
        str(frontend_file.parent),
        cache_headers=False,
    )

    hass.components.frontend.async_register_built_in_panel(
        component_name="custom",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        frontend_url_path=PANEL_URL,
        config={
            "_panel_custom": {
                "name": "wfd-panel",
                "embed_iframe": False,
            }
        },
    )
