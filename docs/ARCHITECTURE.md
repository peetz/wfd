# What's For Dinner? (WFD)

## Overview

What's For Dinner? (WFD) is a Home Assistant custom integration that helps households decide what to eat using a fair, transparent and explainable voting system.

Rather than randomly selecting meals or relying on one person to decide, WFD allows each eligible household member to vote for the meals they would like. A selection engine then generates the next meal plan by balancing votes with historical data to encourage variety while respecting family preferences.

The guiding principle of WFD is simple:

> **Answer one question well: "What's for dinner?"**

---

# Guiding Decisions

When making design decisions, ask:

1. Does this help answer "What's for dinner?"
2. Does it make the app easier to use?
3. Can the decision be explained to the user?
4. Can it be configured without YAML?
5. Is this essential for v1.0?

If the answer to question 5 is "no", it belongs in the roadmap instead of the current milestone.

---

# Goals

Version 1.0 aims to provide:

- Meal management
- Family voting
- Fair meal selection
- Meal history
- Home Assistant notifications
- Native Home Assistant user interface
- HACS compatibility

---

# Design Principles

The project follows these principles.

## Home Assistant First

WFD is designed specifically for Home Assistant.

It should feel like a native part of Home Assistant rather than an external application.

---

## Simple Before Clever

Prefer simple, maintainable solutions over complex ones.

If a feature adds complexity without solving a real problem, it should wait for a future release.

---

## Explain Every Decision

The selection engine must always be able to explain why a meal was selected (or not selected).

Every score adjustment should have a recorded reason.

---

## Preserve History

Meal history should never be lost.

Meals should be archived rather than deleted wherever possible.

Historical meal plans should remain valid even if meals are renamed or archived.

---

## Configuration Through UI

Users should never need to edit YAML.

All settings should be configurable through the Home Assistant interface.

---

## Build in Vertical Slices

Development should deliver visible functionality at every milestone.

Each issue should end with something the user can actually see or use.

---

# Version 1.0 Scope

## Included

### Meals

- Add meal
- Edit meal
- Archive meal
- Restore archived meal
- Emoji
- Recipe text
- Notes

### Users

- Link voters to Home Assistant users
- Enable/disable voters

### Voting

- Configurable voting window
- One vote per meal
- Number of votes equals meals to generate
- Remaining vote indicator

### Planning

- Generate next X meals
- Configurable number of meals
- Explainable selection algorithm

### History

- Generated meal plans
- Vote totals
- Score breakdown
- Selection reasons

### Notifications

- Voting opened
- Voting reminder
- Voting closing
- Meal plan generated

---

## Explicitly Excluded from v1

These are future features and should not delay version 1.0.

- Shopping lists
- Pantry inventory
- AI suggestions
- Calendar integration
- Recipe importing
- Meal photos
- Nutrition tracking
- Mobile app

---

# Workflow

```text
Meals
    │
    ▼
Voting Opens
    │
    ▼
Users Vote
    │
    ▼
Voting Closes
    │
    ▼
Selection Engine
    │
    ▼
Meal Plan Generated
    │
    ▼
History Saved
    │
    ▼
Votes Reset
```

---

# Core Objects

The application revolves around six primary objects.

## Meal

Represents a single meal.

Attributes will eventually include:

- Name
- Emoji
- Recipe
- Notes
- Active / Archived

---

## User

Represents an eligible Home Assistant user.

Attributes include:

- Home Assistant User ID
- Enabled
- Notification Target

---

## Vote

Represents a single user's vote for a meal.

Rules:

- One vote per meal
- Number of votes equals meals to generate

---

## Plan

Represents a generated meal plan.

Contains:

- Selected meals
- Generated date
- Configuration used
- Score explanations

---

## History

Stores all previous plans together with the data used to generate them.

---

## Settings

Stores user configurable behaviour.

Examples:

- Meals to generate
- Voting window
- Selection weighting
- Tie-break behaviour

---

# Selection Engine

The selection engine is responsible for generating the next meal plan.

## Inputs

- Votes
- Meal history
- Previous selections
- Configuration

## Outputs

- Selected meals
- Full score breakdown
- Explanation for every adjustment

---

## Scoring

The exact scoring algorithm will evolve.

Initially:

```
Final Score

=

Votes

+

Bonuses

-

Penalties
```

Future versions will allow configurable weighting.

---

## Tie Breaking

Ties are resolved in the following order:

1. Highest votes
2. Highest average rating
3. Longest since last selected
4. Least selected overall
5. Random

---

## Explainability

Every score adjustment must be recorded.

Example:

```
Pizza

Votes: 3

Adjustments

- Picked last week (-2)

- Picked frequently (-1)

+ Highly rated (+1)

Final Score: 1
```

The explanation should always be available in the history.

---

# Folder Structure

```
custom_components/
└── wfd/
    ├── __init__.py
    ├── manifest.json
    ├── config_flow.py
    ├── const.py
    ├── coordinator.py
    ├── services.py
    ├── frontend/
    ├── database/
    ├── models/
    ├── selector/
    ├── notifications/
    └── translations/
```

This structure may evolve during development.

---

# Development Workflow

Development follows a feature-based approach.

```
Issue

↓

Develop

↓

Test

↓

Review

↓

Merge

↓

Release
```

Each issue should produce a visible improvement.

---

# Roadmap

## v0.1

- Integration skeleton
- Sidebar page

## v0.2

- Database
- Meal management

## v0.3

- Home Assistant users
- Voting

## v0.4

- Selection engine

## v0.5

- History
- Notifications

## v1.0

- Public release
- HACS submission

---

# Future Ideas

Ideas intentionally deferred until after version 1.0.

- Shopping list generation
- Pantry management
- AI meal recommendations
- Meal photographs
- Calendar scheduling
- Multiple households
- Recipe import
- Statistics dashboard
- Seasonal meal suggestions
- Public API

---

# Project Philosophy

WFD is **not** intended to become a complete recipe manager or shopping application.

Its purpose is to solve one problem exceptionally well:

> **Help households fairly decide what to eat next.**

Everything else is secondary.
