# Scrape-Based (Polling) Pattern

**Category:** Infra / Architectural
**File:** `scrape_based.py`

## Intent

Periodically **pull** state from a source at a fixed interval, rather
than waiting for the source to push updates. The consumer controls the
cadence; the source doesn't need to know anything about who's watching.

## When to use it

- **Prometheus-style metrics collection** — this file's exact model: an
  HTTP `/metrics` endpoint per target, scraped on a schedule
- Health checks / uptime monitors hitting a `/healthz` endpoint every N
  seconds
- Any integration with a system that has no webhook/push support and
  must be polled (many legacy APIs, some cloud provider status APIs)
- Batch/cron-driven infra jobs (nightly sync, periodic cleanup)

## How it works (this file)

- `MetricsTarget` — a simulated service exposing `/metrics` (CPU,
  memory, request count), values fluctuate randomly like real telemetry.
- `TimeSeriesStore` — where scraped samples land, mirroring Prometheus's
  TSDB (`latest_for`, `history_for`).
- `Scraper` — the core loop: `scrape_once()` hits every target, records
  a `Sample`, and checks a threshold (simple alerting). `run(cycles)`
  simulates the scheduler that calls `scrape_once()` repeatedly forever
  in production.

## Key interview talking points

- **Pull vs. push (contrast with `event_driven.py`):** polling is
  **simple and self-healing** — if you miss a scrape, the next one just
  happens on schedule, no lost-event problem. The cost is **latency**
  (you only find out about a change up to one interval late) and
  **wasted work** (you scrape even when nothing changed).
- **Interval tuning is a real trade-off:** shorter interval = fresher
  data but more load on both scraper and targets; longer interval =
  less load but staler data and slower alerting. This is a common
  infra interview follow-up ("how would you choose the scrape
  interval?").
- **Cardinality/scale concerns:** at scale (thousands of targets),
  scraping needs to be parallelized/sharded — Prometheus itself uses
  federation and remote-write for this. Mention this if asked "how does
  this scale?"
- **Missed scrapes = gaps, not failures:** unlike event-driven systems
  where a dropped event can be silently lost forever, a failed scrape in
  a polling system just shows up as a data gap and resolves itself next
  cycle — an important reliability property to call out.
- **Where it's a bad fit:** anything needing near-real-time reactions
  (e.g. "page on-call the second a node dies") is much better served by
  the Event-driven or Watcher patterns — polling adds latency by design.

## Run it

```bash
python3 scrape_based.py
```
