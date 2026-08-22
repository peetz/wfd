"""WFD Home Assistant integration."""

from .services import async_setup_services


async def async_setup_entry(hass, entry):
    """Set up WFD from a config entry."""
    await async_setup_services(hass, hass.data[entry.entry_id]["meal_library"])
    return True
