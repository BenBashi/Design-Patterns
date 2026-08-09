# Watcher Pattern

**Category:** Infra / Architectural
**File:** `watcher.py`

## Intent

Maintain a **long-lived subscription** to a resource or stream, receive a
continuous feed of change events (ADD/MODIFY/DELETE), and keep a
**local cache in sync** with the source of truth — reacting via callbacks
as changes arrive.

## When to use it

- The Kubernetes `watch` API (`kubectl get pods --watch`) and client-go's
  Informer/Lister machinery — this file's exact model
- Any controller that needs an up-to-date local view of remote state
  without re-fetching everything on every read (etcd watches, ZooKeeper
  watches, Consul blocking queries)
- Config hot-reloading — watch a config resource, apply changes live
  without restarting

## How it works (this file)

- `WatchEvent` / `ChangeType` — ADDED / MODIFIED / DELETED, mirroring
  Kubernetes watch semantics exactly.
- `PodApiServer` — simulates the source of truth (like the k8s API
  server) and exposes `stream_events(from_index)`, resumable from an
  index — analogous to `resourceVersion` in real k8s watches, letting a
  watcher reconnect after a drop without missing events.
- `PodWatcher` — subscribes to the stream via `sync()`, updates
  `_local_cache` to mirror server state, and fires `on_add` / `on_modify`
  / `on_delete` callbacks. `watcher.cache` is the **local mirror** —
  reads never hit the API server.
- Demo builds a tiny "restart unhealthy pods" controller: it reacts to a
  pod entering `CrashLoopBackOff` via the `on_modify` callback.

## Key interview talking points

- **Watcher vs. Event-driven:** a Watcher tracks **one resource type's
  full state/history** for **one consumer** building a local mirror. An
  event bus (`event_driven.py`) is general-purpose fan-out pub/sub for
  many independent consumers reacting to many different event types.
  Kubernetes actually uses both: watches feed an Informer's local cache,
  and controllers built on top react to Informer callbacks — the
  Informer is essentially "Watcher wrapping a local store."
- **Watcher vs. Scrape-based (polling):** Watcher is push-based over one
  persistent connection (low latency, efficient — no wasted requests
  when nothing changes); polling is pull-based on an interval (simpler,
  self-healing, but higher latency and wasted work). This file exists
  specifically to contrast with `scrape_based.py`.
- **Resume tokens matter:** real watch connections drop (network blips,
  server restarts). `stream_events(from_index=...)` models the
  `resourceVersion` mechanism k8s uses so a reconnecting watcher can
  resume exactly where it left off instead of missing events or
  re-processing everything.
- **The "Informer cache" payoff:** because `PodWatcher.cache` is a local
  mirror, controllers can read current state instantly with **zero API
  calls** — this is why Kubernetes controllers can run thousands of
  reconcile loops without hammering the API server.
- **Watcher feeds Reconcile:** in real k8s controllers, the Watcher/
  Informer triggers a **Reconcile** loop (see `reconcile.py`) whenever it
  sees a change — Watcher says "something changed," Reconcile decides
  "what should I do about it."

## Run it

```bash
python3 watcher.py
```
