# WFD Persistence

## Persistence approach

WFD uses Home Assistant's native `Store` helper for persistent domain data.

This keeps WFD:

- local-first
- independent of external databases
- compatible with Home Assistant's storage location and lifecycle
- separated from the domain model and decision engine

The storage layer is the boundary between WFD domain objects and the persistence mechanism.

```text
Domain Models
     |
     v
 WFD Storage
     |
     v
Home Assistant Store
```

## Schema version

The initial storage schema is version `1`. Future changes must provide an explicit migration path so existing WFD history is preserved.

## Stored data

The storage document contains collections for:

- users
- meals
- voting rounds
- votes
- round results

Completed voting rounds and their results are historical records and must not be modified once completed.

Derived statistics are intentionally not authoritative persisted data. They can be rebuilt from stored rounds, votes and results.

## Scope

This document describes the persistence boundary introduced by Issue #3. Decision-engine rules, Home Assistant services and frontend behaviour remain separate concerns.
