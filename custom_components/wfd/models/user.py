"""Household voter domain model."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Voter:
    """A Home Assistant Person who participates in WFD voting."""

    id: str
    name: str
    active: bool = True


# Kept as a compatibility alias for the existing voting-round model.
User = Voter
