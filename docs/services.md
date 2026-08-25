# WFD Services and Events

WFD exposes services in the `wfd` domain.

## Services

- `wfd.start_voting`: administrator-only; starts a private round. `meals_required` and `deadline_minutes` are optional and use the configured defaults.
- `wfd.submit_vote`: submits an immutable vote for the signed-in Home Assistant user linked to a Person.
- `wfd.cancel_voting`: administrator-only; cancels an active round and permanently removes the round, its votes, and any associated results. Cancellation is only available while the round is open. Rounds close automatically when all voters have submitted or the deadline has passed.
- `wfd.add_meal`, `wfd.rename_meal`, `wfd.archive_meal`, `wfd.restore_meal`: manage meals.
- `wfd.add_voter`, `wfd.archive_voter`, `wfd.restore_voter`: manage household voters.

The `sensor.wfd_voting` entity exposes progress while a round is active and ranked result details after completion. Individual votes and voter identities are never exposed.

## Events

WFD fires these Home Assistant events:

- `wfd_voting_started`: `round_id`, `meals_required`, `voter_count`, `voting_deadline`
- `wfd_voting_completed`: `round_id`, `selected_meals`, `meals_required`
- `wfd_results_available`: `round_id`, `selected_meals`, `meals_required`
- `wfd_voting_cancelled`: `round_id`

Event payloads contain no individual votes. Cancellation is not written to round history; the cancellation event is only a transient notification.
