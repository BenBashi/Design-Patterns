# Event-Driven Pattern

**Category:** Infra / Architectural
**File:** `event_driven.py`

## Intent

Components communicate by publishing and subscribing to **events**
instead of calling each other directly. Producers don't know who (if
anyone) consumes their events; consumers don't know who produced them.
Everything is decoupled through a bus/broker.

## When to use it

- Kubernetes events (`kubectl get events`), CloudWatch Events/EventBridge,
  Kafka/SNS/SQS topic-based systems
- CI/CD pipelines triggering downstream steps (build finished → deploy
  starts)
- Autoscalers, alerting systems, audit logging — anything that needs to
  react to infra state changes **the instant they happen**, without
  polling
- Microservice-to-microservice communication where tight coupling via
  direct calls would create a fragile dependency graph

## How it works (this file)

- `Event` — a typed message (`type`, `payload`, `timestamp`).
- `EventBus` — the broker. `subscribe(event_type, handler)` registers
  interest; `publish(event)` fans the event out to every matching
  subscriber.
- `Deployer` — a **publisher**. It emits `pod.created` and `node.down`
  events but has zero knowledge of who's listening.
- `Autoscaler`, `AlertingSystem`, `AuditLogger` — independent
  **subscribers**, each reacting only to the event types they care
  about. You can add/remove any of them without touching `Deployer`.

## Key interview talking points

- **Push vs. pull:** Event-driven is a **push** model (consumers are
  notified immediately). Contrast with the Scrape-based/polling pattern
  (`scrape_based.py`), which is a **pull** model (consumers check
  periodically). Push is lower-latency but requires reliable delivery;
  pull is simpler and self-healing (a missed poll just happens again
  next cycle) but adds latency and load.
- **Decoupling is the whole point:** the `Deployer` never imports or
  references `Autoscaler`/`AlertingSystem`. New consumers can be added
  with zero changes to the producer — critical in infra where dozens of
  systems react to the same underlying state changes.
- **At-least-once vs. exactly-once delivery:** production event
  buses (Kafka, SQS) usually guarantee at-least-once delivery, meaning
  consumers must be **idempotent** — processing the same event twice
  should be safe. Worth mentioning proactively.
- **Ordering guarantees** are often weaker than people assume — Kafka
  guarantees order only within a partition, not globally. Infra systems
  reacting to events (e.g. "node.down" then "node.up") need to handle
  out-of-order or duplicate delivery gracefully.
- **Failure isolation:** if one subscriber (`AlertingSystem`) throws an
  exception, it shouldn't block others (`AuditLogger`) — in production
  this is handled by dispatching to each handler asynchronously/in
  isolation (e.g. separate consumer groups), not synchronously like this
  simplified demo.

## Run it

```bash
python3 event_driven.py
```
