"""WFD Home Assistant integration."""

from __future__ import annotations

from .services import async_setup_services
from .storage import WFDStorage
from .meal_library import MealLibrary

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: "HomeAssistant", entry: "ConfigEntry"):
    """Set up WFD from a config entry."""
    storage = WFDStorage(hass)
    await storage.async_load()

    meal_library = MealLibrary(storage)

    hass.data.setdefault("wfd", {})[entry.entry_id] = {
        "storage": storage,
        "meal_library": meal_library,
    }

    await async_setup_services(hass, meal_library)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: "HomeAssistant", entry: "ConfigEntry"):
    """Unload WFD."""
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    hass.data.get("wfd", {}).pop(entry.entry_id, None)
    return True
