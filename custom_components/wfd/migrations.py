"""Schema migration helpers for WFD persistent data."""

from __future__ import annotations

from typing import Any, Callable

Migration = Callable[[dict[str, Any]], dict[str, Any]]


CURRENT_SCHEMA_VERSION = 1


def migrate(data: dict[str, Any], from_version: int, to_version: int = CURRENT_SCHEMA_VERSION) -> dict[str, Any]:
    """Migrate persisted WFD data between schema versions."""
    if from_version > to_version:
        raise ValueError("Stored schema version is newer than the supported version")

    migrated = data
    for version in range(from_version, to_version):
        migration = MIGRATIONS.get(version)
        if migration is None:
            raise ValueError(f"No migration registered from schema version {version}")
        migrated = migration(migrated)

    return migrated


def _migrate_v0_to_v1(data: dict[str, Any]) -> dict[str, Any]:
    """Migrate the initial unversioned structure to schema version 1."""
    return {
        "users": data.get("users", {}),
        "meals": data.get("meals", {}),
        "rounds": data.get("rounds", {}),
        "votes": data.get("votes", []),
        "results": data.get("results", []),
    }


MIGRATIONS: dict[int, Migration] = {
    0: _migrate_v0_to_v1,
}
