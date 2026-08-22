"""Meal domain model."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Meal:
    """A selectable WFD meal."""

    id: str
    name: str
    active: bool = True
