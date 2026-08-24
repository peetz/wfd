"""Household voter management for WFD."""

from __future__ import annotations

try:
    from homeassistant.core import EVENT_STATE_CHANGED
except ModuleNotFoundError:
    EVENT_STATE_CHANGED = "state_changed"

from .errors import VoterNotFoundError, VoterUnavailableError
from .models import Voter
from .storage import WFDStorage



class Household:
    """Manage WFD voters backed by Home Assistant Person entities."""

    def __init__(self, hass, storage: WFDStorage) -> None:
        self._hass = hass
        self._storage = storage
        self._remove_state_listener = None

    async def async_start(self) -> None:
        await self.async_sync()
        if self._remove_state_listener is None and hasattr(self._hass, "bus"):
            self._remove_state_listener = self._hass.bus.async_listen(EVENT_STATE_CHANGED, self._async_handle_state_changed)

    async def async_stop(self) -> None:
        if self._remove_state_listener is not None:
            self._remove_state_listener()
            self._remove_state_listener = None

    async def _async_handle_state_changed(self, event) -> None:
        entity_id = event.data.get("entity_id")
        if entity_id and entity_id.startswith("person."):
            await self.async_sync()

    def async_get_available_persons(self) -> list[dict[str, str]]:
        persons = []
        for state in self._hass.states.async_all():
            if state.entity_id.startswith("person."):
                persons.append({"id": state.entity_id, "name": state.name})
        return sorted(persons, key=lambda person: person["name"].casefold())

    async def async_sync(self) -> list[Voter]:
        persons = self.async_get_available_persons()
        existing_voters = {voter.id: voter for voter in await self._storage.async_get_users()}
        voters = []
        for person in persons:
            existing = existing_voters.get(person["id"])
            if existing is None:
                existing = Voter(id=person["id"], name=person["name"], active=True)
                await self._storage.async_set_user(existing)
            elif existing.active and existing.name != person["name"]:
                existing = Voter(id=existing.id, name=person["name"], active=True)
                await self._storage.async_set_user(existing)
            voters.append(existing)
        return voters

    async def async_get_voters(self, active_only: bool = True) -> list[Voter]:
        voters = await self._storage.async_get_users()
        return [voter for voter in voters if voter.active] if active_only else voters

    async def async_get_voter_for_user(self, ha_user_id: str | None) -> Voter | None:
        """Resolve a Home Assistant user to their linked Person voter."""
        if not ha_user_id:
            return None
        for state in self._hass.states.async_all():
            if not state.entity_id.startswith("person."):
                continue
            if getattr(state, "attributes", {}).get("user_id") != ha_user_id:
                continue
            voter = await self._storage.async_get_user(state.entity_id)
            if voter and voter.active:
                return voter
        return None

    async def async_is_admin_user(self, ha_user_id: str | None) -> bool:
        """Return whether the HA user is an administrator in Home Assistant."""
        if not ha_user_id or not hasattr(self._hass, "auth"):
            return False
        user = await self._hass.auth.async_get_user(ha_user_id)
        return bool(user and user.is_admin)

    async def async_add_voter(self, person_id: str) -> Voter:
        person = self._find_person(person_id)
        existing = await self._storage.async_get_user(person_id)
        if existing is not None:
            return existing if existing.active else await self.async_restore_voter(person_id)
        voter = Voter(id=person_id, name=person["name"])
        await self._storage.async_set_user(voter)
        return voter

    async def async_archive_voter(self, person_id: str) -> Voter:
        voter = await self._get_voter(person_id)
        if not voter.active:
            return voter
        archived = Voter(id=voter.id, name=voter.name, active=False)
        await self._storage.async_set_user(archived)
        return archived

    async def async_restore_voter(self, person_id: str) -> Voter:
        person = self._find_person(person_id)
        voter = await self._get_voter(person_id)
        if voter.active:
            return voter
        restored = Voter(id=person_id, name=person["name"], active=True)
        await self._storage.async_set_user(restored)
        return restored

    async def _get_voter(self, person_id: str) -> Voter:
        voter = await self._storage.async_get_user(person_id)
        if voter is None:
            raise VoterNotFoundError(f"Unknown WFD voter: {person_id}")
        return voter

    def _find_person(self, person_id: str) -> dict[str, str]:
        for person in self.async_get_available_persons():
            if person["id"] == person_id:
                return person
        raise VoterUnavailableError(f"Home Assistant Person not found: {person_id}")
