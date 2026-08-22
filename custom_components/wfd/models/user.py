"""Household voter domain model."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class User:
    """A household member who may participate in WFD voting."""

    id: str
    name: str
    active: bool = True
