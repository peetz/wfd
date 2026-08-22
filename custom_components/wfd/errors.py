"""Domain and service errors for WFD."""


class WFDServiceError(Exception):
    """Base class for expected WFD service errors."""


class MealNotFoundError(WFDServiceError):
    """Raised when a requested meal does not exist."""


class DuplicateMealError(WFDServiceError):
    """Raised when a meal name conflicts with another meal."""


class InvalidMealNameError(WFDServiceError):
    """Raised when a meal name is empty or otherwise invalid."""


class VoterNotFoundError(WFDServiceError):
    """Raised when a requested WFD voter does not exist."""


class VoterUnavailableError(WFDServiceError):
    """Raised when a WFD voter does not map to a current HA Person."""
