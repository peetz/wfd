# WFD Decision Engine Rules

When a voting round closes, WFD ranks the active meals deterministically and selects exactly `meals_required` meals.

## Ranking priority

1. Current-round vote score
2. Historical score
3. Recency score
4. Meal name, case-insensitive
5. Meal ID

A lower-priority value never overrides a higher-priority value.

## Scores

### Current-round vote score

`votes_received / number_of_voters`

A round with no voters contributes zero.

### Historical score

For each completed round, calculate the meal's normalised vote score using that round's voter count. The historical score is the arithmetic mean across completed rounds. Zero-vote rounds therefore remain part of the calculation.

### Recency score

For a meal selected in the most recent completed round:

`1 / rounds_since_last_selection`

A meal selected in the immediately preceding round scores `1.0`. Older selections score less. A meal with no selection history scores `0.0`.

Recency is based on the final selected results, not simply on receiving votes.

## Results

Every stored result contains the component scores, rank and a plain-language explanation. Meal name and ID provide stable tie-breaking when all scores are equal.

Archived meals are excluded from the decision.
