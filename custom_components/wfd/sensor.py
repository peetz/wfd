"""WFD sensor entities."""

from __future__ import annotations

try:
    from homeassistant.components.sensor import SensorEntity
except ModuleNotFoundError:
    class SensorEntity:
        """Test fallback when Home Assistant is unavailable."""


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up WFD sensors."""
    data = hass.data["wfd"][entry.entry_id]
    async_add_entities([
        WFDMealLibrarySensor(data["meal_library"]),
        WFDHouseholdSensor(data["household"]),
    ])


class WFDMealLibrarySensor(SensorEntity):
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
        return {
            "meals": [
                {
                    "id": meal.id,
                    "name": meal.name,
                    "active": meal.active,
                }
                for meal in self._meals
            ]
        }

    async def async_update(self):
        self._meals = await self._meal_library.async_get_meals()


class WFDHouseholdSensor(SensorEntity):
    """Expose active and archived WFD household voters."""

    _attr_name = "WFD Household"

    def __init__(self, household):
        self._household = household
        self._attr_unique_id = "wfd_household"
        self._voters = []

    @property
    def native_value(self):
        return len([voter for voter in self._voters if voter.active])

    @property
    def extra_state_attributes(self):
        return {
            "active": [voter.name for voter in self._voters if voter.active],
            "archived": [voter.name for voter in self._voters if not voter.active],
        }

    async def async_update(self):
        self._voters = await self._household.async_get_voters(active_only=False)
