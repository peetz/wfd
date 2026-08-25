# What's For Dinner (WFD)

WFD is a Home Assistant integration for managing household meals, running private voting rounds, and selecting dinner through a deterministic, explainable decision engine.

## V1.0

WFD 1.0 provides the complete core workflow inside Home Assistant:

- HACS-installable custom integration with configuration flow
- Meal library with add, rename, archive, and restore
- Household voters backed by Home Assistant Persons
- Administrator-only round management
- Private, immutable voting as the signed-in Home Assistant user
- Configurable meals-per-round and voting deadline
- Automatic round completion
- Deterministic, explainable decision ranking using current votes, historical support, recency, and stable tie-breaking
- Persisted round history and results
- Responsive Home Assistant panel for meals, household, voting, progress, and results
- Documented services and privacy-safe lifecycle events
- Immediate state refresh after successful WFD actions

## Installation and setup

See [docs/installation.md](docs/installation.md).

## Decision rules

See [docs/decision-engine.md](docs/decision-engine.md).

## Services and events

See [docs/services.md](docs/services.md).

## Development

Run the test suite with:

```bash
python -m pytest
```

## V1.1 roadmap

Planned follow-up work includes notifications, richer history analytics, frontend polish and UX refinement, expanded automation APIs, and optional reusable Lovelace widgets. These are tracked in the V1.1 GitHub milestone and do not change the core V1 workflow.
