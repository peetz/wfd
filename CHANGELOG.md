# Changelog

All notable changes to What's For Dinner (WFD) will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/) and versions follow semantic versioning.

## [1.0.0] - 2026-08-25

First distributable WFD release.

### Added

- Home Assistant custom integration with HACS support and configuration flow.
- Meal library management with add, rename, archive, restore, and persistence.
- Home Assistant Person-backed household voters with archive and restore management.
- Private voting rounds for signed-in Home Assistant users.
- Configurable meals-per-round and voting deadline defaults.
- Automatic round completion when all voters have voted or the deadline is reached.
- Deterministic, explainable decision engine using current votes, historical support, recency, and stable tie-breaking.
- Persisted round history and result details.
- Home Assistant services and privacy-safe lifecycle events.
- Responsive Home Assistant application panel covering meals, household, voting, progress, and results.

### Fixed

- Immediate entity refresh after WFD actions without relying on normal Home Assistant polling.
- Reliable repeated frontend panel registration during reloads and upgrades.

## [Unreleased]

V1.1 work is tracked in GitHub issues and includes notifications, richer analytics, frontend polish, and expanded automation APIs.

[1.0.0]: https://github.com/peetz/wfd/releases/tag/v1.0.0
[Unreleased]: https://github.com/peetz/wfd/compare/v1.0.0...develop
