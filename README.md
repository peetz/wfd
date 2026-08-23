# What's For Dinner (WFD)

A Home Assistant integration to help families decide what's for dinner by combining meal planning, household voting, and future recommendation features.

## Overview

WFD is designed to answer a simple question:

> What's for dinner?

It provides the foundations for a family meal decision system inside Home Assistant.

Current capabilities:

- Meal library management
- Persistent meal storage
- Household voters sourced from Home Assistant People
- Voter archive and restore support

Planned capabilities:

- Voting rounds
- Meal selection workflows
- Results and history
- Meal recommendations based on household preferences

## Architecture

WFD keeps Home Assistant as the source of truth for household identity:

```
Home Assistant People
        |
        v
    WFD Voters
        |
        v
 Voting Rounds
        |
        v
 Results & History
```

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

## Project Status

WFD is being developed incrementally with each feature tracked as a GitHub milestone/issue.

## License

See [LICENSE](LICENSE).
