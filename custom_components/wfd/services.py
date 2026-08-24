"""Home Assistant services for WFD."""

from typing import TYPE_CHECKING

from .errors import DuplicateMealError, InvalidMealNameError, MealNotFoundError, VoterNotFoundError, VoterUnavailableError
from .updates import async_signal_update

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall

DOMAIN = "wfd"
ADD_MEAL = "add_meal"
RENAME_MEAL = "rename_meal"
ARCHIVE_MEAL = "archive_meal"
RESTORE_MEAL = "restore_meal"
ADD_VOTER = "add_voter"
ARCHIVE_VOTER = "archive_voter"
RESTORE_VOTER = "restore_voter"
START_VOTING = "start_voting"
SUBMIT_VOTE = "submit_vote"
CLOSE_VOTING = "close_voting"


def _raise_service_error(exc: Exception) -> Exception:
    from homeassistant.exceptions import HomeAssistantError
    if isinstance(exc, (MealNotFoundError, DuplicateMealError, InvalidMealNameError, VoterNotFoundError, VoterUnavailableError)):
        return HomeAssistantError(str(exc))
    return exc


async def async_setup_services(hass: "HomeAssistant", meal_library, household, voting=None) -> None:
    """Register WFD services."""
    async def call(method, call):
        try:
            await method(call)
            async_signal_update(hass)
        except Exception as exc:
            raise _raise_service_error(exc) from exc

    async def add_meal(call):
        await call(meal_library.async_add_meal, call.data["name"])

    async def rename_meal(call):
        await call(meal_library.async_rename_meal, call.data["meal_id"], call.data["name"])

    async def archive_meal(call):
        await call(meal_library.async_archive_meal, call.data["meal_id"])

    async def restore_meal(call):
        await call(meal_library.async_restore_meal, call.data["meal_id"])

    async def add_voter(call):
        await call(household.async_add_voter, call.data["person_id"])

    async def archive_voter(call):
        await call(household.async_archive_voter, call.data["person_id"])

    async def restore_voter(call):
        await call(household.async_restore_voter, call.data["person_id"])

    hass.services.async_register(DOMAIN, ADD_MEAL, add_meal)
    hass.services.async_register(DOMAIN, RENAME_MEAL, rename_meal)
    hass.services.async_register(DOMAIN, ARCHIVE_MEAL, archive_meal)
    hass.services.async_register(DOMAIN, RESTORE_MEAL, restore_meal)
    hass.services.async_register(DOMAIN, ADD_VOTER, add_voter)
    hass.services.async_register(DOMAIN, ARCHIVE_VOTER, archive_voter)
    hass.services.async_register(DOMAIN, RESTORE_VOTER, restore_voter)

    if voting is None:
        return

    async def start_voting(call):
        await voting.async_create_round(call.data["meals_required"], call.data.get("deadline_minutes", 1440))

    async def submit_vote(call):
        await voting.async_submit_vote(call.data["round_id"], call.data["user_id"], call.data["meal_ids"])

    async def close_voting(call):
        await voting.async_close_round(call.data["round_id"])

    hass.services.async_register(DOMAIN, START_VOTING, start_voting)
    hass.services.async_register(DOMAIN, SUBMIT_VOTE, submit_vote)
    hass.services.async_register(DOMAIN, CLOSE_VOTING, close_voting)
