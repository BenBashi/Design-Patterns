"""
WATCHER PATTERN
==================
Category : Infra / Architectural
Interview tag: "Maintain a long-lived subscription to a resource/stream
                and invoke callbacks as change events arrive, keeping a
                local view in sync with a source of truth."

Real-world infra use case in this file
----------------------------------------
This mirrors the Kubernetes `watch` API (`kubectl get pods --watch`,
or client-go's Informer/Watcher machinery): instead of polling
`GET /pods` every N seconds (scrape_based.py) or fully decoupling via a
pub/sub bus (event_driven.py), a Watcher opens ONE long-lived connection
to a resource and receives a continuous STREAM of ADD/MODIFY/DELETE
events, using them to keep a local cache in sync.

Key distinction from Event-driven: a Watcher is about *one consumer
tracking one resource's full change history/state*, often maintaining a
local mirror (informer cache) — not a general fan-out pub/sub bus.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Iterator


# ---------------------------------------------------------------------------
# Change event types — mirrors k8s watch semantics: ADDED / MODIFIED / DELETED
# ---------------------------------------------------------------------------
class ChangeType(Enum):
    ADDED = "ADDED"
    MODIFIED = "MODIFIED"
    DELETED = "DELETED"


@dataclass
class WatchEvent:
    change_type: ChangeType
    resource_id: str
    resource: dict | None  # None for DELETED after removal, otherwise the object


# ---------------------------------------------------------------------------
# The "source of truth" — simulates an API server / etcd stream. In real
# Kubernetes this would be a long-lived HTTP connection with chunked
# transfer encoding streaming JSON watch events.
# ---------------------------------------------------------------------------
class PodApiServer:
    def __init__(self):
        self._pods: dict[str, dict] = {}
        self._watch_log: list[WatchEvent] = []

    def create_pod(self, pod_id: str, spec: dict) -> None:
        self._pods[pod_id] = spec
        self._watch_log.append(WatchEvent(ChangeType.ADDED, pod_id, dict(spec)))

    def update_pod(self, pod_id: str, spec: dict) -> None:
        self._pods[pod_id] = spec
        self._watch_log.append(WatchEvent(ChangeType.MODIFIED, pod_id, dict(spec)))

    def delete_pod(self, pod_id: str) -> None:
        self._pods.pop(pod_id, None)
        self._watch_log.append(WatchEvent(ChangeType.DELETED, pod_id, None))

    def stream_events(self, from_index: int = 0) -> Iterator[WatchEvent]:
        """Simulates a long-lived watch stream, yielding events as they
        happened, starting from a resume point (`from_index`) — analogous
        to a Kubernetes `resourceVersion` used to resume a watch after a
        disconnect without missing events."""
        yield from self._watch_log[from_index:]

    @property
    def event_count(self) -> int:
        return len(self._watch_log)


# ---------------------------------------------------------------------------
# The Watcher — subscribes to the stream, maintains a local cache
# (an "informer" in k8s terms), and invokes callbacks on change.
# ---------------------------------------------------------------------------
class PodWatcher:
    def __init__(self, api_server: PodApiServer):
        self._api_server = api_server
        self._local_cache: dict[str, dict] = {}
        self._last_seen_index = 0
        self._on_add: list[Callable[[str, dict], None]] = []
        self._on_modify: list[Callable[[str, dict], None]] = []
        self._on_delete: list[Callable[[str], None]] = []

    def on_add(self, handler: Callable[[str, dict], None]) -> None:
        self._on_add.append(handler)

    def on_modify(self, handler: Callable[[str, dict], None]) -> None:
        self._on_modify.append(handler)

    def on_delete(self, handler: Callable[[str], None]) -> None:
        self._on_delete.append(handler)

    def sync(self) -> None:
        """Pulls any new events off the stream since we last checked and
        applies them to the local cache + fires callbacks. In a real
        Watcher this method isn't called manually — it's driven by the
        open streaming connection pushing events as they arrive."""
        for event in self._api_server.stream_events(from_index=self._last_seen_index):
            self._apply(event)
        self._last_seen_index = self._api_server.event_count

    def _apply(self, event: WatchEvent) -> None:
        if event.change_type == ChangeType.ADDED:
            self._local_cache[event.resource_id] = event.resource
            print(f"[Watcher] ADD {event.resource_id}: {event.resource}")
            for h in self._on_add:
                h(event.resource_id, event.resource)

        elif event.change_type == ChangeType.MODIFIED:
            self._local_cache[event.resource_id] = event.resource
            print(f"[Watcher] MODIFY {event.resource_id}: {event.resource}")
            for h in self._on_modify:
                h(event.resource_id, event.resource)

        elif event.change_type == ChangeType.DELETED:
            self._local_cache.pop(event.resource_id, None)
            print(f"[Watcher] DELETE {event.resource_id}")
            for h in self._on_delete:
                h(event.resource_id)

    @property
    def cache(self) -> dict:
        """The local mirror of resource state — reads never hit the API
        server, unlike scrape-based polling. This is the 'informer cache'
        pattern used heavily throughout Kubernetes controllers."""
        return dict(self._local_cache)


# ---------------------------------------------------------------------------
# Demo — a naive "restart unhealthy pods" controller built on top of the
# Watcher, reacting to MODIFY events instead of polling for status.
# ---------------------------------------------------------------------------
def _demo():
    api_server = PodApiServer()
    watcher = PodWatcher(api_server)

    watcher.on_add(lambda pid, spec: print(f"  -> [Controller] noticed new pod {pid}"))
    watcher.on_modify(
        lambda pid, spec: print(f"  -> [Controller] pod {pid} changed, status={spec.get('status')}")
        or (print(f"  -> [Controller] 🔁 restarting unhealthy pod {pid}") if spec.get("status") == "CrashLoopBackOff" else None)
    )
    watcher.on_delete(lambda pid: print(f"  -> [Controller] pod {pid} removed from cache"))

    print("--- API server creates two pods (watcher hasn't synced yet) ---")
    api_server.create_pod("web-1", {"image": "nginx:1.25", "status": "Running"})
    api_server.create_pod("web-2", {"image": "nginx:1.25", "status": "Running"})

    print("\n--- Watcher syncs: catches up on all events so far ---")
    watcher.sync()
    print("Local cache:", watcher.cache)

    print("\n--- API server updates a pod to a bad state ---")
    api_server.update_pod("web-2", {"image": "nginx:1.25", "status": "CrashLoopBackOff"})
    watcher.sync()

    print("\n--- API server deletes a pod ---")
    api_server.delete_pod("web-1")
    watcher.sync()
    print("Local cache after delete:", watcher.cache)


if __name__ == "__main__":
    _demo()
