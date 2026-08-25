# WFD Home Assistant Services and Events

WFD exposes services in the `wfd` domain. The WFD panel uses the same services and entities; business logic is not duplicated in the frontend.

## Voting services

- `wfd.start_voting` — administrator-only. Starts a private round. `meals_required` and `deadline_minutes` are optional and use the configured defaults.
- `wfd.submit_vote` — submits the signed-in Home Assistant user's immutable vote. The user must be linked to a WFD voter Person.
- `wfd.cancel_voting` — administrator-only. Cancels an active round and removes its transient round data. Cancellation is not added to voting history.

Rounds close automatically when all eligible voters have submitted their votes or when the deadline is reached.

## Meal services

- `wfd.add_meal`
- `wfd.rename_meal`
- `wfd.archive_meal`
- `wfd.restore_meal`

## Household services

- `wfd.add_voter`
- `wfd.archive_voter`
- `wfd.restore_voter`

## Voting state

`sensor.wfd_voting` exposes public voting progress while a round is active and ranked result details after completion. Individual votes and voter identities are never exposed through the sensor.

## Events

WFD fires these Home Assistant events:

- `wfd_voting_started`: `round_id`, `meals_required`, `voter_count`, `voting_deadline`
- `wfd_voting_completed`: `round_id`, `selected_meals`, `meals_required`
- `wfd_results_available`: `round_id`, `selected_meals`, `meals_required`
- `wfd_voting_cancelled`: `round_id`

Event payloads contain no individual votes. Cancellation is a transient event only and does not create a historical round.
