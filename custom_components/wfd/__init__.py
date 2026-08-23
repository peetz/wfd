"""WFD Home Assistant integration."""

from __future__ import annotations

import inspect

from .frontend import async_register_frontend
from .household import Household
from .meal_library import MealLibrary
from .services import async_setup_services
from .storage import WFDStorage

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: "HomeAssistant", entry: "ConfigEntry"):
    """Set up WFD from a config entry."""
    storage = WFDStorage(hass)
    await storage.async_load()
    meal_library = MealLibrary(storage)
    household = Household(hass, storage)
    await household.async_start()

    hass.data.setdefault("wfd", {})[entry.entry_id] = {
        "storage": storage,
        "meal_library": meal_library,
        "household": household,
    }

    await async_setup_services(hass, meal_library, household)
    async_register_frontend(hass)

    forward_setups = getattr(hass.config_entries, "async_forward_entry_setups", None)
    if inspect.iscoroutinefunction(forward_setups):
        await forward_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: "HomeAssistant", entry: "ConfigEntry"):
    """Unload WFD."""
    data = hass.data.get("wfd", {}).get(entry.entry_id)
    if data is not None:
        await data["household"].async_stop()

    unload_platforms = getattr(hass.config_entries, "async_unload_platforms", None)
    if inspect.iscoroutinefunction(unload_platforms):
        await unload_platforms(entry, PLATFORMS)
    hass.data.get("wfd", {}).pop(entry.entry_id, None)
    return True
