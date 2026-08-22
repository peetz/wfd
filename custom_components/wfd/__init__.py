"""WFD Home Assistant integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .services import async_setup_services
from .storage import WFDStorage
from .meal_library import MealLibrary


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up WFD from a config entry."""
    storage = WFDStorage(hass)
    await storage.async_load()

    meal_library = MealLibrary(storage)

    hass.data.setdefault("wfd", {})[entry.entry_id] = {
        "storage": storage,
        "meal_library": meal_library,
    }

    await async_setup_services(hass, meal_library)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload WFD."""
    hass.data.get("wfd", {}).pop(entry.entry_id, None)
    return True
