# WFD Domain Model & Data Schema

## Purpose

This document defines the V1 domain model used by WFD. The models are framework-independent so the persistence layer can store them without coupling core business rules to Home Assistant internals.

## Entities

### User

Represents a household voter.

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Stable WFD identifier |
| `name` | string | Display name |
| `active` | boolean | Whether the user can participate in new rounds |

Historical rounds retain the user IDs that participated, so later household membership changes do not alter historical voter counts.

### Meal

Represents a selectable meal.

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Stable WFD identifier |
| `name` | string | Meal name |
| `active` | boolean | Whether the meal is available for new voting rounds |

Meals contain no recipe, ingredient, nutrition, shopping or preparation data in the domain model.

### VotingRound

Represents one complete meal-selection process.

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Stable round identifier |
| `number` | integer | Sequential round number; primary recency reference |
| `created_at` | datetime | Round creation time |
| `voting_deadline` | datetime | Deadline for accepting votes |
| `closed_at` | datetime or null | Time the round closed |
| `meals_required` | integer | Number of meals the decision engine must select |
| `voter_ids` | tuple of strings | Users recorded as participants in the round |
| `status` | enum | Round lifecycle state |

The voter count is derived from `voter_ids` rather than treated as an independent source of truth.

Lifecycle states are:

1. `created`
2. `active`
3. `closed`
4. `decision_generated`
5. `results_stored`

Completed rounds are intended to be immutable once stored.

### Vote

Represents one private user-to-meal choice within a round.

| Field | Type | Meaning |
|---|---|---|
| `round_id` | string | Voting round containing the vote |
| `user_id` | string | User who cast the vote |
| `meal_id` | string | Meal selected by the user |

Persistence must enforce uniqueness of `(round_id, user_id, meal_id)`. V1 does not support vote changes.

Business validation must also enforce the per-user vote limit and one-vote-per-meal rule for an active round.

### RoundResult

Represents the decision-engine output for a meal in a completed round.

| Field | Type | Meaning |
|---|---|---|
| `round_id` | string | Source voting round |
| `meal_id` | string | Candidate meal |
| `selected` | boolean | Whether the meal was selected |
| `decision_score` | number | Final engine score |
| `vote_score` | number | Normalised current-round vote score |
| `historical_score` | number | Historical normalised vote score |
| `recency_score` | number | Score contribution based on selection recency |
| `rank` | integer | Decision ranking within the round |
| `explanation` | string | Human-readable reason for the outcome |

Results are a set of selected meals, not an assigned calendar schedule. Ranking is for explanation and display only.

## Relationships

```text
User ───────< Vote >────── Meal
  │             │            │
  │             │            │
  └──── participant ──── VotingRound
                              │
                              └────< RoundResult >──── Meal
```

A `VotingRound` records its participating `User` IDs. `Vote` records the user and meal selected. `RoundResult` records the decision-engine output for the round and meal.

## Historical Calculations

Historical values are derived from completed rounds. Raw round, vote and result data remains the source of truth.

For a completed round:

`round_vote_score = votes_received / voter_count`

A meal receiving zero votes receives a score of `0` and remains included in historical calculations.

A meal's historical score is the arithmetic mean of its normalised round vote scores across completed rounds, including zero-vote rounds.

Selection recency uses the sequential round number:

`rounds_since_chosen = current_round_number - last_chosen_round_number`

The source of truth for `last_chosen_round_number` is the most recent completed round in which the meal has a selected `RoundResult`.

## Derived and Cached Values

The following values may be cached later for performance but are not authoritative:

- historical score
- last chosen round
- rounds since chosen
- total votes
- times chosen
- selection frequency

All cached values must be rebuildable from historical round data.

## Persistence Boundary

Issue 01 defines the domain contract only. Database tables, migrations, serialization and storage implementation belong to issue 02.
