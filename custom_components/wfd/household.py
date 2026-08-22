"""Household voter management for WFD."""

from __future__ import annotations

from .errors import VoterNotFoundError, VoterUnavailableError
from .models import Voter
from .storage import WFDStorage


class Household:
    """Manage WFD voters backed by Home Assistant Person entities."""

    def __init__(self, hass, storage: WFDStorage) -> None:
        self._hass = hass
        self._storage = storage

    def async_get_available_persons(self) -> list[dict[str, str]]:
        """Return Home Assistant Persons available to become WFD voters."""
        persons = []
        for state in self._hass.states.async_all():
            if not state.entity_id.startswith("person."):
                continue
            persons.append({"id": state.entity_id, "name": state.name})
        return sorted(persons, key=lambda person: person["name"].casefold())

    async def async_get_voters(self, active_only: bool = True) -> list[Voter]:
        """Return active voters by default, or the complete voter list."""
        voters = await self._storage.async_get_users()
        if active_only:
            return [voter for voter in voters if voter.active]
        return voters

    async def async_add_voter(self, person_id: str) -> Voter:
        """Add a Home Assistant Person as an active WFD voter."""
        person = self._find_person(person_id)
        existing = await self._storage.async_get_user(person_id)
        if existing is not None:
            if existing.active:
                return existing
            return await self.async_restore_voter(person_id)

        voter = Voter(id=person_id, name=person["name"])
        await self._storage.async_set_user(voter)
        return voter

    async def async_archive_voter(self, person_id: str) -> Voter:
        """Archive a voter without deleting their identity."""
        voter = await self._get_voter(person_id)
        if not voter.active:
            return voter
        archived = Voter(id=voter.id, name=voter.name, active=False)
        await self._storage.async_set_user(archived)
        return archived

    async def async_restore_voter(self, person_id: str) -> Voter:
        """Restore an archived voter if their HA Person still exists."""
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
