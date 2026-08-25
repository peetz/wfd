# Decision Engine Rules

The decision engine ranks every active meal when a voting round closes.

## Priority

Ranking is lexicographic and deterministic:

1. Current-round vote score
2. Historical score
3. Recency score
4. Meal name, case-insensitive
5. Meal ID

Lower-priority values never override a higher-priority value.

## Scores

### Current-round vote score

`votes_received / number_of_voters`

A round with no voters contributes zero.

### Historical score

For every completed round, calculate the meal's normalised vote score using that round's voter count. The historical score is the arithmetic mean across all completed rounds. A meal with no votes in a completed round contributes zero, so zero-vote rounds remain part of the calculation.

### Recency score

For a meal selected in the most recent completed round:

`1 / rounds_since_last_selection`

A meal selected in the immediately preceding round scores `1.0`. Older selections score less. A meal with no selection history scores `0.0`.

Recency is based on final selected results, not merely receiving a vote.

## Selection and explanations

Meals are sorted by the priority order above and exactly `meals_required` meals are marked selected. Every stored result contains all component scores, its rank, and a plain-language explanation. Name and ID provide stable results when all decision scores tie.

Archived meals are excluded from the decision.
