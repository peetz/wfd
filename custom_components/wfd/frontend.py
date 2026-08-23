"""Frontend registration helpers for WFD."""

from __future__ import annotations

from pathlib import Path


FRONTEND_PATH = "/wfd/frontend"
PANEL_URL = "wfd"
PANEL_TITLE = "What's For Dinner"
PANEL_ICON = "mdi:silverware-fork-knife"
PANEL_MODULE_URL = f"{FRONTEND_PATH}/wfd-panel.js"


async def async_register_frontend(hass) -> None:
    """Register the WFD sidebar panel.

    The panel intentionally contains no business logic. It is a presentation
    layer over WFD entities and services.
    """
    from homeassistant.components import frontend
    from homeassistant.components.http import StaticPathConfig

    frontend_file = Path(__file__).parent / "frontend" / "wfd-panel.js"

    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                url_path=FRONTEND_PATH,
                path=str(frontend_file.parent),
                cache_headers=False,
            )
        ]
    )

    frontend.async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        frontend_url_path=PANEL_URL,
        config={
            "_panel_custom": {
                "name": "wfd-panel",
                "module_url": PANEL_MODULE_URL,
                "embed_iframe": False,
            }
        },
    )
