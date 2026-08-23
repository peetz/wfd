"""Tests for Home Assistant Person-backed household voters."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from .household import Household
from .models import Voter
from .storage import WFDStorage


class FakeState:
    def __init__(self, entity_id: str, name: str) -> None:
        self.entity_id = entity_id
        self.name = name


@pytest.fixture
def storage() -> WFDStorage:
    storage = object.__new__(WFDStorage)
    storage._store = MagicMock()
    storage._store.async_save = AsyncMock()
    storage._data = storage._empty_data()
    return storage


def household(storage: WFDStorage) -> Household:
    hass = MagicMock()
    hass.states.async_all.return_value = [
        FakeState("person.steve", "Steve"),
        FakeState("person.clare", "Clare"),
        FakeState("light.kitchen", "Kitchen"),
    ]
    return Household(hass, storage)


def test_discovers_home_assistant_persons(storage: WFDStorage) -> None:
    result = household(storage).async_get_available_persons()
    assert result == [
        {"id": "person.clare", "name": "Clare"},
        {"id": "person.steve", "name": "Steve"},
    ]


@pytest.mark.asyncio
async def test_auto_discovery_includes_new_person_and_preserves_archive(storage: WFDStorage) -> None:
    service = household(storage)

    await service.async_sync()
    await service.async_archive_voter("person.clare")

    service._hass.states.async_all.return_value.append(FakeState("person.evelyn", "Evelyn"))
    await service.async_sync()

    assert await service.async_get_voters() == [
        Voter(id="person.steve", name="Steve"),
        Voter(id="person.evelyn", name="Evelyn"),
    ]
    assert sorted(await service.async_get_voters(active_only=False), key=lambda voter: voter.id) == [
        Voter(id="person.clare", name="Clare", active=False),
        Voter(id="person.evelyn", name="Evelyn"),
        Voter(id="person.steve", name="Steve"),
    ]


@pytest.mark.asyncio
async def test_start_registers_listener_and_stop_removes_it(storage: WFDStorage) -> None:
    service = household(storage)
    remove_listener = MagicMock()
    service._hass.bus.async_listen.return_value = remove_listener

    await service.async_start()

    service._hass.bus.async_listen.assert_called_once()
    assert service._remove_state_listener is remove_listener

    await service.async_stop()

    remove_listener.assert_called_once()
    assert service._remove_state_listener is None


@pytest.mark.asyncio
async def test_add_archive_and_restore_voter(storage: WFDStorage) -> None:
    service = household(storage)

    voter = await service.async_add_voter("person.steve")
    assert voter == Voter(id="person.steve", name="Steve")

    archived = await service.async_archive_voter("person.steve")
    assert archived.active is False

    restored = await service.async_restore_voter("person.steve")
    assert restored == voter


@pytest.mark.asyncio
async def test_voter_persists_and_active_filter_works(storage: WFDStorage) -> None:
    service = household(storage)
    await service.async_add_voter("person.steve")
    await service.async_add_voter("person.clare")
    await service.async_archive_voter("person.clare")

    assert await service.async_get_voters() == [Voter(id="person.steve", name="Steve")]
    assert await service.async_get_voters(active_only=False) == [
        Voter(id="person.steve", name="Steve"),
        Voter(id="person.clare", name="Clare", active=False),
    ]


@pytest.mark.asyncio
async def test_unknown_person_cannot_be_added(storage: WFDStorage) -> None:
    service = household(storage)
    with pytest.raises(Exception, match="Home Assistant Person not found"):
        await service.async_add_voter("person.unknown")


@pytest.mark.asyncio
async def test_household_sensor_contract_data(storage: WFDStorage) -> None:
    service = household(storage)
    await service.async_sync()
    await service.async_archive_voter("person.clare")

    voters = await service.async_get_voters(active_only=False)
    available = service.async_get_available_persons()

    assert sorted(
        [
            {"id": voter.id, "name": voter.name, "active": voter.active}
            for voter in voters
        ],
        key=lambda voter: voter["id"],
    ) == [
        {"id": "person.clare", "name": "Clare", "active": False},
        {"id": "person.steve", "name": "Steve", "active": True},
    ]
    assert available == [
        {"id": "person.clare", "name": "Clare"},
        {"id": "person.steve", "name": "Steve"},
    ]
