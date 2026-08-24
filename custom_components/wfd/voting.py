"""Voting round domain helpers for WFD."""


class VotingSelectionError(ValueError):
    """Raised when a voter selects an invalid number of meals."""


def validate_selection(selected_meal_ids: list[str], required_count: int) -> None:
    """Validate that a voter selected exactly the required number of meals."""
    if len(selected_meal_ids) != required_count:
        raise VotingSelectionError(
            f"Select exactly {required_count} meals"
        )

    if len(set(selected_meal_ids)) != len(selected_meal_ids):
        raise VotingSelectionError("Duplicate meals are not allowed")
