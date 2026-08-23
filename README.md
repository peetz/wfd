# What's For Dinner (WFD)

A Home Assistant integration to help families decide what's for dinner by combining meal planning, household voting, and future recommendation features.

## Overview

WFD answers a simple question:

> What's for dinner?

It provides the foundations for a family meal decision system inside Home Assistant.

## Current capabilities

- Meal library management
- Persistent meal storage
- Home Assistant People integration for household voters
- Voter archive and restore support
- Custom Home Assistant frontend panel foundation

## Planned capabilities

- Meal Library UI
- Household management UI
- Voting rounds
- Meal voting workflows
- Results and history
- Meal recommendations based on household preferences
- Optional Lovelace widgets

## Frontend architecture

WFD uses an application-style custom Home Assistant panel as the primary user experience.

```
                 WFD Core
                    |
        +-----------+-----------+
        |                       |
   Custom Panel          Lovelace Widgets
   (primary UX)           (future option)
```

The custom panel provides a full app experience while Lovelace widgets remain a future option for dashboard users who want WFD data embedded elsewhere.

## Development workflow

Changes are developed incrementally through GitHub issues and pull requests.

Standard workflow:

1. Review the issue and confirm scope.
2. Create a feature branch.
3. Implement the change.
4. Add or update tests.
5. Open a pull request.
6. Merge after CI passes.
7. Update documentation and release notes.

## Installation

This project is currently under active development and is not yet published through HACS.

For development/testing:

1. Copy `custom_components/wfd` into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. Configure the integration from Home Assistant.

## Development

Clone the repository:

```bash
git clone https://github.com/peetz/wfd.git
cd wfd
```

Run tests:

```bash
python -m pytest
```

## Project status

WFD is being developed incrementally with features tracked through GitHub milestones and issues.

See:

- `docs/` for project documentation
- GitHub Issues for planned work
- Pull Requests for completed changes

## License

See [LICENSE](LICENSE).
