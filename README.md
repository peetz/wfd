# What's For Dinner (WFD)

WFD is a Home Assistant integration for managing household meals, running private voting rounds, and selecting dinner through a deterministic, explainable decision engine.

## V1.0 capabilities

- Installable as a custom integration through HACS.
- Meal library with archive and restore.
- Home Assistant Person-backed household voters.
- Administrator-only round management using Home Assistant administrator accounts.
- Private, immutable voting as the signed-in user.
- Configurable default meal count and voting deadline.
- Deterministic decision ranking using current votes, historical support, recency, and stable tie-breaking.
- Persisted round history and explainable results.
- Responsive Home Assistant panel for meals, household, voting, progress, and results.
- Documented Home Assistant services and privacy-safe lifecycle events.

## Install

See [docs/installation.md](docs/installation.md) for HACS installation, first setup, upgrades, and backup/recovery.

## Decision behaviour

See [docs/decision-engine.md](docs/decision-engine.md) for the scoring and tie-breaking rules.

## Services and events

See [docs/services.md](docs/services.md) for service fields, lifecycle events, and privacy guarantees.

## Development

Run the test suite with:

```bash
python -m pytest
```

## V1.1

Notifications, rich history analytics, frontend polish, expanded automation APIs, and optional Lovelace widgets are planned for v1.1.
