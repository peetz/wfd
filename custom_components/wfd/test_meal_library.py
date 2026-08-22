"""Tests for the WFD meal library."""

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from .errors import DuplicateMealError, InvalidMealNameError, MealNotFoundError
from .meal_library import MealLibrary
from .models import Meal, RoundResult, VotingRound
from .models.voting_round import VotingRoundStatus
from .storage import WFDStorage


@pytest.fixture
def storage() -> WFDStorage:
    """Return an isolated WFD storage instance."""
    storage = object.__new__(WFDStorage)
    storage._store = MagicMock()
    storage._store.async_load = AsyncMock(return_value=None)
    storage._store.async_save = AsyncMock()
    storage._data = storage._empty_data()
    return storage


@pytest.fixture
def library(storage: WFDStorage) -> MealLibrary:
    """Return a meal library using the isolated storage fixture."""
    return MealLibrary(storage)


@pytest.mark.asyncio
async def test_add_meal_trims_name_and_creates_active_meal(library: MealLibrary) -> None:
    """New meals receive an ID, trimmed name and active status."""
    meal = await library.async_add_meal("  Pizza  ")

    assert meal.name == "Pizza"
    assert meal.active is True
    assert meal.id


@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["", "   ", "\t\n"])
async def test_add_meal_rejects_empty_name(library: MealLibrary, name: str) -> None:
    """Blank meal names are rejected."""
    with pytest.raises(InvalidMealNameError):
        await library.async_add_meal(name)


@pytest.mark.asyncio
async def test_add_meal_rejects_case_insensitive_duplicate(library: MealLibrary) -> None:
    """Meal names are unique regardless of case."""
    await library.async_add_meal("Pizza")

    with pytest.raises(DuplicateMealError):
        await library.async_add_meal(" pizza ")


@pytest.mark.asyncio
async def test_rename_meal_allows_active_and_archived_meals(library: MealLibrary) -> None:
    """Existing meals can be renamed regardless of active status."""
    meal = await library.async_add_meal("Pizza")
    renamed = await library.async_rename_meal(meal.id, "Pasta")
    assert renamed == Meal(id=meal.id, name="Pasta", active=True)

    archived = await library.async_archive_meal(meal.id)
    renamed_archived = await library.async_rename_meal(archived.id, "Lasagne")
    assert renamed_archived == Meal(id=meal.id, name="Lasagne", active=False)


@pytest.mark.asyncio
async def test_rename_meal_rejects_duplicate_name(library: MealLibrary) -> None:
    """Renaming cannot collide with another meal."""
    first = await library.async_add_meal("Pizza")
    second = await library.async_add_meal("Pasta")

    with pytest.raises(DuplicateMealError):
        await library.async_rename_meal(second.id, first.name.upper())


@pytest.mark.asyncio
async def test_archive_and_restore_are_idempotent(library: MealLibrary) -> None:
    """Repeated archive and restore operations leave the same state."""
    meal = await library.async_add_meal("Pizza")

    archived = await library.async_archive_meal(meal.id)
    archived_again = await library.async_archive_meal(meal.id)
    assert archived_again == archived

    restored = await library.async_restore_meal(meal.id)
    restored_again = await library.async_restore_meal(meal.id)
    assert restored_again == restored
    assert restored.active is True


@pytest.mark.asyncio
async def test_restore_rechecks_name_uniqueness(storage: WFDStorage) -> None:
    """A restored meal cannot conflict with another meal's name."""
    library = MealLibrary(storage)
    first = await library.async_add_meal("Pizza")
    second = await library.async_add_meal("Pasta")
    await library.async_archive_meal(first.id)

    # Simulate a legacy/corrupt persisted state that introduced a collision.
    storage._data["meals"][first.id]["name"] = second.name

    with pytest.raises(DuplicateMealError):
        await library.async_restore_meal(first.id)


@pytest.mark.asyncio
async def test_unknown_meal_raises(library: MealLibrary) -> None:
    """Unknown IDs produce an explicit domain error."""
    with pytest.raises(MealNotFoundError):
        await library.async_get_meal("missing")

    with pytest.raises(MealNotFoundError):
        await library.async_archive_meal("missing")


@pytest.mark.asyncio
async def test_get_meals_defaults_to_active_only(library: MealLibrary) -> None:
    """Active retrieval excludes archived meals by default."""
    active = await library.async_add_meal("Pizza")
    archived = await library.async_add_meal("Pasta")
    archived = await library.async_archive_meal(archived.id)

    assert await library.async_get_meals() == [active]
    assert await library.async_get_meals(active_only=False) == [active, archived]


@pytest.mark.asyncio
async def test_meals_persist_across_save_and_load(storage: WFDStorage) -> None:
    """A meal survives a storage save/load cycle as a domain object."""
    library = MealLibrary(storage)
    meal = await library.async_add_meal("Pizza")
    saved_data = deepcopy(storage._data)

    restored_storage = object.__new__(WFDStorage)
    restored_storage._store = MagicMock()
    restored_storage._store.async_load = AsyncMock(return_value=saved_data)
    restored_storage._store.async_save = AsyncMock()
    restored_storage._data = restored_storage._empty_data()

    await restored_storage.async_load()

    restored = await MealLibrary(restored_storage).async_get_meal(meal.id)
    assert restored == meal


@pytest.mark.asyncio
async def test_archiving_meal_does_not_alter_historical_results(
    storage: WFDStorage,
    library: MealLibrary,
) -> None:
    """Archiving a meal preserves historical round references and results."""
    meal = await library.async_add_meal("Pizza")
    created = datetime.now(UTC)
    round_ = VotingRound(
        id="round-1",
        number=1,
        created_at=created,
        voting_deadline=created + timedelta(days=1),
        meals_required=1,
        status=VotingRoundStatus.RESULTS_STORED,
    )
    storage._data["rounds"][round_.id] = {
        "id": round_.id,
        "number": round_.number,
        "created_at": round_.created_at.isoformat(),
        "voting_deadline": round_.voting_deadline.isoformat(),
        "meals_required": round_.meals_required,
        "voter_ids": [],
        "closed_at": None,
        "status": round_.status.value,
    }
    result = RoundResult(
        round_id=round_.id,
        meal_id=meal.id,
        selected=True,
        decision_score=1.0,
        vote_score=1.0,
        historical_score=0.5,
        recency_score=0.25,
        rank=1,
        explanation="Selected.",
    )
    storage._data["results"].append(
        {
            "round_id": result.round_id,
            "meal_id": result.meal_id,
            "selected": result.selected,
            "decision_score": result.decision_score,
            "vote_score": result.vote_score,
            "historical_score": result.historical_score,
            "recency_score": result.recency_score,
            "rank": result.rank,
            "explanation": result.explanation,
        }
    )
    before = deepcopy(storage._data["results"])

    await library.async_archive_meal(meal.id)

    assert storage._data["results"] == before
    assert (await library.async_get_meal(meal.id)).active is False
