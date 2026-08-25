"""WFD sensor entities."""

from __future__ import annotations

try:
    from homeassistant.components.sensor import SensorEntity
except ModuleNotFoundError:
    class SensorEntity:
        """Test fallback."""

from .updates import SIGNAL_WFD_UPDATED


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up WFD sensors."""
    data = hass.data["wfd"][entry.entry_id]
    entities = [
        WFDMealLibrarySensor(hass, data["meal_library"]),
        WFDHouseholdSensor(hass, data["household"]),
        WFDVotingSensor(hass, data["voting"]),
    ]
    for entity in entities:
        entity._wfd_entry_id = entry.entry_id
    hass.data["wfd"].setdefault("_entities", []).extend(entities)
    async_add_entities(entities)


class WFDBaseSensor(SensorEntity):
    """Common WFD sensor behaviour."""

    def __init__(self, hass):
        self._hass = hass

    def _refresh(self):
        """Refresh and publish the entity without waiting for HA polling."""
        self._hass.async_create_task(self._async_refresh())

    async def _async_refresh(self) -> None:
        await self.async_update()
        self.async_write_ha_state()


class WFDMealLibrarySensor(WFDBaseSensor):
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
        return {"voters": [{"id": v.id, "name": v.name, "active": v.active} for v in self._voters], "available_persons": self._available_persons}

    async def async_update(self):
        self._voters = await self._household.async_get_voters(active_only=False)
        self._available_persons = self._household.async_get_available_persons()


class WFDVotingSensor(WFDBaseSensor):
    """Expose round progress and completion state without private votes."""

    _attr_name = "WFD Voting"

    def __init__(self, hass, voting):
        super().__init__(hass)
        self._voting = voting
        self._attr_unique_id = "wfd_voting"
        self._state = {}

    @property
    def native_value(self):
        return self._state.get("status", "idle")

    @property
    def extra_state_attributes(self):
        return self._state

    async def async_update(self):
        self._state = await self._voting.async_get_public_state()
