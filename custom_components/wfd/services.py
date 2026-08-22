"""Home Assistant services for WFD."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall
    from .household import Household
    from .meal_library import MealLibrary

from .errors import DuplicateMealError, InvalidMealNameError, MealNotFoundError, VoterNotFoundError, VoterUnavailableError

DOMAIN = "wfd"
ADD_MEAL = "add_meal"
RENAME_MEAL = "rename_meal"
ARCHIVE_MEAL = "archive_meal"
RESTORE_MEAL = "restore_meal"
ADD_VOTER = "add_voter"
ARCHIVE_VOTER = "archive_voter"
RESTORE_VOTER = "restore_voter"


def _raise_service_error(exc: Exception) -> Exception:
    from homeassistant.exceptions import HomeAssistantError
    if isinstance(exc, (MealNotFoundError, DuplicateMealError, InvalidMealNameError, VoterNotFoundError, VoterUnavailableError)):
        return HomeAssistantError(str(exc))
    return exc


async def async_setup_services(hass: "HomeAssistant", meal_library: "MealLibrary", household: "Household" | None = None) -> None:
    """Register WFD meal and household management services."""
    async def add_meal(call: "ServiceCall") -> None:
        try:
            await meal_library.async_add_meal(call.data["name"])
        except Exception as exc:
            raise _raise_service_error(exc) from exc

    async def rename_meal(call: "ServiceCall") -> None:
        try:
            await meal_library.async_rename_meal(call.data["meal_id"], call.data["name"])
        except Exception as exc:
            raise _raise_service_error(exc) from exc

    async def archive_meal(call: "ServiceCall") -> None:
        try:
            await meal_library.async_archive_meal(call.data["meal_id"])
        except Exception as exc:
            raise _raise_service_error(exc) from exc

    async def restore_meal(call: "ServiceCall") -> None:
        try:
            await meal_library.async_restore_meal(call.data["meal_id"])
        except Exception as exc:
            raise _raise_service_error(exc) from exc

    hass.services.async_register(DOMAIN, ADD_MEAL, add_meal)
    hass.services.async_register(DOMAIN, RENAME_MEAL, rename_meal)
    hass.services.async_register(DOMAIN, ARCHIVE_MEAL, archive_meal)
    hass.services.async_register(DOMAIN, RESTORE_MEAL, restore_meal)

    if household is None:
        return

    async def add_voter(call: "ServiceCall") -> None:
        try:
            await household.async_add_voter(call.data["person_id"])
        except Exception as exc:
            raise _raise_service_error(exc) from exc

    async def archive_voter(call: "ServiceCall") -> None:
        try:
            await household.async_archive_voter(call.data["person_id"])
        except Exception as exc:
            raise _raise_service_error(exc) from exc

    async def restore_voter(call: "ServiceCall") -> None:
        try:
            await household.async_restore_voter(call.data["person_id"])
        except Exception as exc:
            raise _raise_service_error(exc) from exc

    hass.services.async_register(DOMAIN, ADD_VOTER, add_voter)
    hass.services.async_register(DOMAIN, ARCHIVE_VOTER, archive_voter)
    hass.services.async_register(DOMAIN, RESTORE_VOTER, restore_voter)
