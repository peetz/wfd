"""Tests for WFD persistence migrations."""

import pytest

from .migrations import CURRENT_SCHEMA_VERSION, migrate


def test_migrate_v0_to_current() -> None:
    """Legacy unversioned data migrates into the v1 structure."""
    data = {
        "users": {"user-1": {"id": "user-1", "name": "Steve", "active": True}},
        "meals": {"meal-1": {"id": "meal-1", "name": "Pizza", "active": True}},
    }

    migrated = migrate(data, 0)

    assert CURRENT_SCHEMA_VERSION == 1
    assert migrated["users"] == data["users"]
    assert migrated["meals"] == data["meals"]
    assert migrated["rounds"] == {}
    assert migrated["votes"] == []
    assert migrated["results"] == []


def test_current_version_requires_no_migration() -> None:
    """Current schema data passes through unchanged."""
    data = {"users": {}, "meals": {}, "rounds": {}, "votes": [], "results": []}

    assert migrate(data, CURRENT_SCHEMA_VERSION) is data


def test_newer_schema_is_rejected() -> None:
    """A future schema version cannot be silently accepted."""
    with pytest.raises(ValueError, match="newer"):
        migrate({}, CURRENT_SCHEMA_VERSION + 1)
