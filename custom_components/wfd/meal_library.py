"""Meal library service for WFD."""

from __future__ import annotations

from uuid import uuid4

from .errors import DuplicateMealError, InvalidMealNameError, MealNotFoundError
from .models import Meal
from .storage import WFDStorage


class MealLibrary:
    """Maintain the meals available to WFD voting."""

    def __init__(self, storage: WFDStorage) -> None:
        """Initialise the meal library with its persistence boundary."""
        self._storage = storage

    async def async_add_meal(self, name: str) -> Meal:
        """Add and persist a new active meal."""
        name = _normalise_name(name)
        await self._ensure_unique_name(name)

        meal = Meal(id=str(uuid4()), name=name)
        await self._storage.async_set_meal(meal)
        return meal

    async def async_rename_meal(self, meal_id: str, name: str) -> Meal:
        """Rename and persist an existing meal."""
        meal = await self._get_existing_meal(meal_id)
        name = _normalise_name(name)
        await self._ensure_unique_name(name, excluding_meal_id=meal.id)

        renamed = Meal(id=meal.id, name=name, active=meal.active)
        await self._storage.async_set_meal(renamed)
        return renamed

    async def async_archive_meal(self, meal_id: str) -> Meal:
        """Archive a meal without deleting it."""
        meal = await self._get_existing_meal(meal_id)
        archived = Meal(id=meal.id, name=meal.name, active=False)
        await self._storage.async_set_meal(archived)
        return archived

    async def async_restore_meal(self, meal_id: str) -> Meal:
        """Restore an archived meal after rechecking name uniqueness."""
        meal = await self._get_existing_meal(meal_id)
        await self._ensure_unique_name(meal.name, excluding_meal_id=meal.id)
        restored = Meal(id=meal.id, name=meal.name, active=True)
        await self._storage.async_set_meal(restored)
        return restored

    async def async_get_meal(self, meal_id: str) -> Meal:
        """Return one meal or raise if it does not exist."""
        return await self._get_existing_meal(meal_id)

    async def async_get_meals(self, active_only: bool = True) -> list[Meal]:
        """Return active meals by default, or the complete library."""
        meals = await self._storage.async_get_meals()
        if active_only:
            return [meal for meal in meals if meal.active]
        return meals

    async def _get_existing_meal(self, meal_id: str) -> Meal:
        """Return a meal or raise the public service error."""
        meal = await self._storage.async_get_meal(meal_id)
        if meal is None:
            raise MealNotFoundError(f"Unknown meal ID: {meal_id}")
        return meal

    async def _ensure_unique_name(
        self,
        name: str,
        *,
        excluding_meal_id: str | None = None,
    ) -> None:
        """Ensure no other meal has the same name, ignoring case."""
        normalised = name.casefold()
        meals = await self._storage.async_get_meals()
        if any(
            meal.id != excluding_meal_id and meal.name.casefold() == normalised
            for meal in meals
        ):
            raise DuplicateMealError(f"Meal already exists: {name}")


def _normalise_name(name: str) -> str:
    """Trim and validate a meal name."""
    if not isinstance(name, str):
        raise InvalidMealNameError("Meal name must be a string")

    normalised = name.strip()
    if not normalised:
        raise InvalidMealNameError("Meal name must not be empty")

    return normalised
