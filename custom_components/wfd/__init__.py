"""WFD Home Assistant integration."""

from __future__ import annotations

import inspect

from .frontend import async_register_frontend
from .household import Household
from .meal_library import MealLibrary
from .services import async_setup_services
from .storage import WFDStorage
from .voting_manager import VotingManager

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: "HomeAssistant", entry: "ConfigEntry"):
    """Set up WFD from a config entry."""
    storage = WFDStorage(hass)
    await storage.async_load()
    meal_library = MealLibrary(storage)
    household = Household(hass, storage)
    await household.async_start()
    voting = VotingManager(
        storage,
        meal_library,
        household,
        default_meals_required=entry.data.get("default_meals_required", 1),
        default_deadline_minutes=entry.data.get("default_deadline_minutes", 1440),
        hass=hass,
    )
    hass.data.setdefault("wfd", {})[entry.entry_id] = {"storage": storage, "meal_library": meal_library, "household": household, "voting": voting}
    await async_setup_services(hass, meal_library, household, voting)
    await async_register_frontend(hass)
    forward_setups = getattr(hass.config_entries, "async_forward_entry_setups", None)
    if inspect.iscoroutinefunction(forward_setups):
        await forward_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: "HomeAssistant", entry: "ConfigEntry"):
    """Unload WFD."""
    data = hass.data.get("wfd", {}).get(entry.entry_id)
    if data is not None:
        await data["household"].async_stop()
        voting = data.get("voting")
        if voting is not None:
            await voting.async_stop()
    unload_platforms = getattr(hass.config_entries, "async_unload_platforms", None)
    if inspect.iscoroutinefunction(unload_platforms):
        await unload_platforms(entry, PLATFORMS)
    wfd_data = hass.data.get("wfd", {})
    entities = wfd_data.get("_entities", [])
    wfd_data["_entities"] = [
        entity for entity in entities
        if getattr(entity, "_wfd_entry_id", None) != entry.entry_id
    ]
    wfd_data.pop(entry.entry_id, None)
    return True
