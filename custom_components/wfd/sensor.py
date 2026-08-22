"""WFD sensor entities."""

from __future__ import annotations


class WFDMealLibrarySensor:
    """Expose the active WFD meal library."""

    _attr_name = "WFD Meal Library"

    def __init__(self, meal_library):
        self._meal_library = meal_library
        self._attr_unique_id = "wfd_meal_library"
        self._meals = []

    @property
    def native_value(self):
        return len(self._meals)

    @property
    def extra_state_attributes(self):
        return {"meals": [meal.name for meal in self._meals]}

    async def async_update(self):
        self._meals = await self._meal_library.async_get_meals()


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up WFD sensors."""
    data = hass.data["wfd"][entry.entry_id]
    async_add_entities([WFDMealLibrarySensor(data["meal_library"])])
