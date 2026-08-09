"""
RECONCILE PATTERN
==================
Category : Infra / Architectural
Interview tag: "Continuously compare DESIRED state to ACTUAL state, and
                take actions to converge actual -> desired. Idempotent,
                level-triggered, self-healing."

Real-world infra use case in this file
----------------------------------------
This is THE core pattern behind every Kubernetes controller (Deployment
controller, ReplicaSet controller, and every custom operator built with
controller-runtime/kubebuilder). We simulate a tiny "ReplicaSet"
controller: the user declares "I want 3 replicas of nginx running," and
a Reconciler loop repeatedly checks actual running pods vs. desired count
and creates/deletes pods to converge — including self-healing after pods
randomly die outside of its control.

Critical property: reconcile is LEVEL-TRIGGERED, not EDGE-TRIGGERED.
It doesn't care WHAT changed or HOW state drifted — every run it just
asks "what's the delta between desired and actual RIGHT NOW" and fixes
it. This makes it naturally self-healing and safe to re-run (idempotent).
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Desired state — what the user/operator declared they want (like a
# Kubernetes Deployment spec).
# ---------------------------------------------------------------------------
@dataclass
class ReplicaSetSpec:
    name: str
    image: str
    desired_replicas: int


# ---------------------------------------------------------------------------
# Actual state — the real world, which can drift out from under us at any
# time (pods crash, get evicted, get manually deleted by an operator...).
# ---------------------------------------------------------------------------
@dataclass
class Pod:
    id: str
    replica_set: str
    image: str
    healthy: bool = True


class ClusterState:
    """Simulates the real cluster: pods can appear/disappear/crash outside
    of the controller's control, just like in real infrastructure."""

    def __init__(self):
        self._pods: dict[str, Pod] = {}

    def running_pods_for(self, replica_set: str) -> list[Pod]:
        return [p for p in self._pods.values()
                if p.replica_set == replica_set and p.healthy]

    def schedule_pod(self, replica_set: str, image: str) -> Pod:
        pod = Pod(id=f"pod-{uuid.uuid4().hex[:6]}", replica_set=replica_set, image=image)
        self._pods[pod.id] = pod
        print(f"    [Cluster] scheduled {pod.id}")
        return pod

    def terminate_pod(self, pod_id: str) -> None:
        self._pods.pop(pod_id, None)
        print(f"    [Cluster] terminated {pod_id}")

    def simulate_random_failure(self, replica_set: str) -> None:
        """Randomly kills a pod to simulate real-world drift (a node dies,
        OOM kill, etc.) — state changes WITHOUT the controller doing it."""
        candidates = self.running_pods_for(replica_set)
        if candidates and random.random() < 0.5:
            victim = random.choice(candidates)
            victim.healthy = False
            print(f"    [Cluster] 💥 {victim.id} crashed unexpectedly (outside controller's control)")


# ---------------------------------------------------------------------------
# The Reconciler — the heart of the pattern.
# ---------------------------------------------------------------------------
class ReplicaSetReconciler:
    def __init__(self, cluster: ClusterState):
        self._cluster = cluster

    def reconcile(self, spec: ReplicaSetSpec) -> None:
        """One reconcile pass: compare desired vs actual, converge.
        Level-triggered: doesn't matter WHY state drifted, only THAT it
        did. Safe to call repeatedly (idempotent) — calling it when
        actual == desired is a harmless no-op."""
        actual_pods = self._cluster.running_pods_for(spec.name)
        actual_count = len(actual_pods)
        desired_count = spec.desired_replicas

        print(f"  [Reconciler] {spec.name}: desired={desired_count}, actual={actual_count}")

        if actual_count == desired_count:
            print("  [Reconciler] state matches desired — no action needed")
            return

        if actual_count < desired_count:
            missing = desired_count - actual_count
            print(f"  [Reconciler] under-provisioned by {missing}, creating pods")
            for _ in range(missing):
                self._cluster.schedule_pod(spec.name, spec.image)

        else:  # actual_count > desired_count
            excess = actual_count - desired_count
            print(f"  [Reconciler] over-provisioned by {excess}, terminating pods")
            for pod in actual_pods[:excess]:
                self._cluster.terminate_pod(pod.id)

    def run_loop(self, spec: ReplicaSetSpec, iterations: int) -> None:
        """In production this runs forever, triggered either by a Watcher
        noticing a change (see watcher.py) or on a periodic re-sync timer
        as a safety net in case events were ever missed."""
        for i in range(iterations):
            print(f"\n=== Reconcile loop iteration {i + 1} ===")
            self._cluster.simulate_random_failure(spec.name)
            self.reconcile(spec)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
def _demo():
    random.seed(7)

    cluster = ClusterState()
    reconciler = ReplicaSetReconciler(cluster)

    spec = ReplicaSetSpec(name="nginx-rs", image="nginx:1.25", desired_replicas=3)

    print("--- Initial state: 0 pods running, desired = 3 ---")
    reconciler.reconcile(spec)  # should create 3 pods

    reconciler.run_loop(spec, iterations=4)  # self-heals after random crashes

    print("\n--- User changes desired_replicas from 3 to 1 (scale down) ---")
    spec.desired_replicas = 1
    reconciler.reconcile(spec)

    print("\n--- Re-running reconcile again with no changes (idempotency check) ---")
    reconciler.reconcile(spec)  # should be a no-op


if __name__ == "__main__":
    _demo()
