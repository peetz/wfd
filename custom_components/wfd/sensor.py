"""WFD sensor entities."""

from __future__ import annotations

try:
    from homeassistant.components.sensor import SensorEntity
    from homeassistant.helpers.dispatcher import async_dispatcher_connect
except ModuleNotFoundError:
    class SensorEntity:
        """Test fallback when Home Assistant is unavailable."""

    def async_dispatcher_connect(*args, **kwargs):
        """Test fallback when Home Assistant is unavailable."""
        return lambda: None

from .updates import SIGNAL_WFD_UPDATED


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up WFD sensors."""
    data = hass.data["wfd"][entry.entry_id]
    async_add_entities([
        WFDMealLibrarySensor(hass, data["meal_library"]),
        WFDHouseholdSensor(hass, data["household"]),
    ])


class WFDBaseSensor(SensorEntity):
    """Common WFD sensor behaviour."""

    def __init__(self, hass):
        self._hass = hass

    async def async_added_to_hass(self):
        self.async_on_remove(
            async_dispatcher_connect(
                self._hass,
                SIGNAL_WFD_UPDATED,
                self._refresh,
            )
        )

    def _refresh(self):
        self.async_schedule_update_ha_state(True)


class WFDMealLibrarySensor(WFDBaseSensor):
    """Expose the WFD meal library including archived meals."""

    _attr_name = "WFD Meal Library"

    def __init__(self, hass, meal_library):
        super().__init__(hass)
        self._meal_library = meal_library
        self._attr_unique_id = "wfd_meal_library"
        self._meals = []

    @property
    def native_value(self):
        return len(self._meals)

    @property
    def extra_state_attributes(self):
        return {"meals": [{"id": m.id, "name": m.name, "active": m.active} for m in self._meals]}

    async def async_update(self):
        self._meals = await self._meal_library.async_get_meals(active_only=False)


class WFDHouseholdSensor(WFDBaseSensor):
    """Expose WFD household voters and available Home Assistant Persons."""

    _attr_name = "WFD Household"

    def __init__(self, hass, household):
        super().__init__(hass)
        self._household = household
        self._attr_unique_id = "wfd_household"
        self._voters = []
        self._available_persons = []

    @property
    def native_value(self):
        return len([voter for voter in self._voters if voter.active])

    @property
    def extra_state_attributes(self):
        return {
            "voters": [{"id": v.id, "name": v.name, "active": v.active} for v in self._voters],
            "available_persons": self._available_persons,
        }

    async def async_update(self):
        self._voters = await self._household.async_get_voters(active_only=False)
        self._available_persons = self._household.async_get_available_persons()
