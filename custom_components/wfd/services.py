"""Home Assistant services for WFD."""

from typing import TYPE_CHECKING

from .errors import DuplicateMealError, InvalidMealNameError, MealNotFoundError, VoterNotFoundError, VoterUnavailableError
from .updates import async_signal_update

try:
    from homeassistant.exceptions import HomeAssistantError
except ModuleNotFoundError:
    class HomeAssistantError(Exception):
        """Test fallback when Home Assistant is unavailable."""

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

DOMAIN = "wfd"
ADD_MEAL, RENAME_MEAL, ARCHIVE_MEAL, RESTORE_MEAL = "add_meal", "rename_meal", "archive_meal", "restore_meal"
ADD_VOTER, ARCHIVE_VOTER, RESTORE_VOTER = "add_voter", "archive_voter", "restore_voter"
START_VOTING, SUBMIT_VOTE, CLOSE_VOTING = "start_voting", "submit_vote", "close_voting"


def _raise_service_error(exc: Exception) -> Exception:
    if isinstance(exc, (MealNotFoundError, DuplicateMealError, InvalidMealNameError, VoterNotFoundError, VoterUnavailableError)):
        return HomeAssistantError(str(exc))
    return exc


async def async_setup_services(hass: "HomeAssistant", meal_library, household=None, voting=None) -> None:
    """Register WFD services."""
    async def run(method, *args):
        try:
            result = await method(*args)
            async_signal_update(hass)
            return result
        except Exception as exc:
            raise _raise_service_error(exc) from exc

    async def require_admin(call):
        if household is None or not await household.async_is_admin_user(getattr(call.context, "user_id", None)):
            raise HomeAssistantError("Only the designated WFD administrator can manage voting rounds")

    async def add_meal(call):
        await run(meal_library.async_add_meal, call.data["name"])

    async def rename_meal(call):
        await run(meal_library.async_rename_meal, call.data["meal_id"], call.data["name"])

    async def archive_meal(call):
        await run(meal_library.async_archive_meal, call.data["meal_id"])

    async def restore_meal(call):
        await run(meal_library.async_restore_meal, call.data["meal_id"])

    for name, handler in ((ADD_MEAL, add_meal), (RENAME_MEAL, rename_meal), (ARCHIVE_MEAL, archive_meal), (RESTORE_MEAL, restore_meal)):
        hass.services.async_register(DOMAIN, name, handler)

    if household is not None:
        async def add_voter(call):
            await run(household.async_add_voter, call.data["person_id"])

        async def archive_voter(call):
            await run(household.async_archive_voter, call.data["person_id"])

        async def restore_voter(call):
            await run(household.async_restore_voter, call.data["person_id"])

        for name, handler in ((ADD_VOTER, add_voter), (ARCHIVE_VOTER, archive_voter), (RESTORE_VOTER, restore_voter)):
            hass.services.async_register(DOMAIN, name, handler)

    if voting is None:
        return

    def fire_event(event_type, data):
        """Fire a privacy-safe WFD lifecycle event when HA is available."""
        if hasattr(hass, "bus") and hasattr(hass.bus, "async_fire"):
            hass.bus.async_fire(event_type, data)

    async def start_voting(call):
        await require_admin(call)
        round_ = await run(
            voting.async_create_round,
            call.data.get("meals_required"),
            call.data.get("deadline_minutes"),
        )
        fire_event(
            "wfd_voting_started",
            {
                "round_id": round_.id,
                "meals_required": round_.meals_required,
                "voter_count": round_.voter_count,
                "voting_deadline": round_.voting_deadline.isoformat(),
            },
        )

    async def submit_vote(call):
        voter = await household.async_get_voter_for_user(getattr(call.context, "user_id", None))
        if voter is None:
            raise HomeAssistantError("Your Home Assistant user is not linked to an active WFD Person")
        await run(voting.async_submit_vote, call.data["round_id"], voter.id, call.data["meal_ids"])

    async def close_voting(call):
        await require_admin(call)
        results = await run(voting.async_close_round, call.data["round_id"])
        round_ = await voting.async_get_round(call.data["round_id"])
        selected_meals = [result.meal_id for result in results if result.selected]
        event_data = {
            "round_id": call.data["round_id"],
            "selected_meals": selected_meals,
            "meals_required": round_.meals_required if round_ else len(selected_meals),
        }
        fire_event("wfd_voting_completed", event_data)
        fire_event("wfd_results_available", event_data)

    for name, handler in ((START_VOTING, start_voting), (SUBMIT_VOTE, submit_vote), (CLOSE_VOTING, close_voting)):
        hass.services.async_register(DOMAIN, name, handler)
