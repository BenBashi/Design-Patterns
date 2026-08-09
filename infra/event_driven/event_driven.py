"""
EVENT-DRIVEN PATTERN
======================
Category : Infra / Architectural
Interview tag: "Components communicate by producing and consuming events
                asynchronously, rather than calling each other directly."

Real-world infra use case in this file
----------------------------------------
A simplified infra event bus, similar in spirit to Kubernetes events,
CloudWatch Events/EventBridge, or a Kafka topic. Infra components
(a Deployer, an Autoscaler, an Alerting system) don't call each other
directly — they publish events ("pod.created", "node.down") to a bus, and
independent subscribers react to what they care about.

This is the opposite of the "Scrape-based" (polling) pattern in
scrape_based.py: here, consumers are *pushed* updates the instant
something happens, instead of *pulling* on a timer.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable


# ---------------------------------------------------------------------------
# Event definition
# ---------------------------------------------------------------------------
@dataclass
class Event:
    type: str          # e.g. "pod.created", "node.down"
    payload: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def __repr__(self):
        return f"Event(type={self.type!r}, payload={self.payload})"


# ---------------------------------------------------------------------------
# Event Bus — the infra backbone. Publishers and subscribers never know
# about each other directly, only about the bus.
# ---------------------------------------------------------------------------
class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable[[Event], None]]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        self._subscribers[event_type].append(handler)
        print(f"[EventBus] {handler.__qualname__} subscribed to '{event_type}'")

    def publish(self, event: Event) -> None:
        print(f"[EventBus] publishing {event}")
        handlers = self._subscribers.get(event.type, [])
        if not handlers:
            print(f"[EventBus] no subscribers for '{event.type}'")
        for handler in handlers:
            # In production this dispatch would be async (e.g. via a
            # message queue / worker pool) so one slow handler can't
            # block others. Kept synchronous here for readability.
            handler(event)


# ---------------------------------------------------------------------------
# Publisher — an infra component that emits events when something happens.
# It has ZERO knowledge of who (if anyone) is listening.
# ---------------------------------------------------------------------------
class Deployer:
    def __init__(self, bus: EventBus):
        self._bus = bus

    def deploy_pod(self, pod_name: str, node: str):
        print(f"[Deployer] deploying {pod_name} to {node}...")
        # ... actual scheduling logic would go here ...
        self._bus.publish(Event("pod.created", {"pod": pod_name, "node": node}))

    def crash_node(self, node: str):
        print(f"[Deployer] {node} went down!")
        self._bus.publish(Event("node.down", {"node": node}))


# ---------------------------------------------------------------------------
# Subscribers — independent infra components reacting to events they care
# about. Each can be added/removed without touching the Deployer at all.
# ---------------------------------------------------------------------------
class Autoscaler:
    """Reacts to pod creation by checking if more capacity is needed."""

    def on_pod_created(self, event: Event) -> None:
        print(f"[Autoscaler] noticed new pod '{event.payload['pod']}' "
              f"on {event.payload['node']} — evaluating scaling policy")


class AlertingSystem:
    """Pages on-call when a node goes down."""

    def on_node_down(self, event: Event) -> None:
        print(f"[AlertingSystem] 🚨 PAGE ON-CALL: node {event.payload['node']} is down!")


class AuditLogger:
    """Logs every infra event for compliance, regardless of type."""

    def __init__(self, bus: EventBus):
        # subscribes to multiple event types individually — a real system
        # might support wildcard subscriptions instead.
        bus.subscribe("pod.created", self.log)
        bus.subscribe("node.down", self.log)

    def log(self, event: Event) -> None:
        print(f"[AuditLogger] recorded event to audit trail: {event}")


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
def _demo():
    bus = EventBus()

    autoscaler = Autoscaler()
    alerting = AlertingSystem()
    AuditLogger(bus)  # subscribes itself in __init__

    bus.subscribe("pod.created", autoscaler.on_pod_created)
    bus.subscribe("node.down", alerting.on_node_down)

    deployer = Deployer(bus)

    print("\n--- Deploying a pod ---")
    deployer.deploy_pod("web-server-7", "node-3")

    print("\n--- Simulating a node crash ---")
    deployer.crash_node("node-3")

    print("\n--- Publishing an event nobody explicitly cares about ---")
    bus.publish(Event("volume.resized", {"volume": "pvc-1", "new_size_gb": 100}))


if __name__ == "__main__":
    _demo()
