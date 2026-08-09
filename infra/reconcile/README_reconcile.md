# Reconcile Pattern

**Category:** Infra / Architectural
**File:** `reconcile.py`

## Intent

Continuously compare **desired state** to **actual state**, and take
whatever actions converge actual toward desired. The reconciler doesn't
care what caused drift — only that it exists — and re-running it when
there's no drift is a safe no-op.

## When to use it

- **This is THE core control loop behind every Kubernetes controller** —
  Deployment, ReplicaSet, StatefulSet controllers, and every custom
  operator built with controller-runtime/kubebuilder
- Infrastructure-as-code tools (Terraform apply, Pulumi) — same idea:
  diff desired config against real cloud state, converge
  - Config drift correction / GitOps (ArgoCD, Flux): repo state = desired,
  cluster state = actual, continuously reconciled
- Any system that must **self-heal** without manual intervention

## How it works (this file)

- `ReplicaSetSpec` — desired state: "I want 3 replicas of `nginx:1.25`."
- `ClusterState` — actual state, which can drift **outside the
  controller's control** (`simulate_random_failure` randomly kills pods,
  just like real crashes/evictions).
- `ReplicaSetReconciler.reconcile(spec)` — the core loop: fetch actual
  pod count, compare to desired, create pods if under-provisioned,
  terminate if over-provisioned, do nothing if they match.
- `run_loop` simulates repeated reconciliation with random failures
  injected each iteration — the reconciler keeps healing the deployment
  back to 3 replicas without ever being told "a pod crashed."
- Demo also shows a scale-down (desired 3 → 1) and a **no-op reconcile**
  to prove idempotency.

## Key interview talking points

- **Level-triggered vs. edge-triggered — the single most important
  concept here.** Edge-triggered means "react to the specific event that
  just happened" (fragile — if you miss an event, state is wrong
  forever). Level-triggered means "look at the current state and always
  ask what needs fixing, regardless of history" — self-healing by
  construction, and safe even if a controller crashes and misses events
  entirely.
- **Idempotency:** calling `reconcile()` when actual already equals
  desired is a harmless no-op. This is what makes it safe to call
  reconcile on *every* watch event, on a periodic timer, AND after a
  controller restart, without side effects piling up.
- **Reconcile is usually triggered by Watcher, backed by periodic
  re-sync:** in real k8s controllers, a Watcher/Informer (`watcher.py`)
  triggers `reconcile()` the instant something changes, but controllers
  *also* run a periodic full re-sync (e.g. every 30s) as a safety net in
  case a watch event was ever dropped — this file's `run_loop` models
  that repeated-check behavior.
- **Reconcile vs. imperative "do this action" systems:** an imperative
  system says "run `create_pod()`" as a one-time command — if it fails
  or is skipped, nothing retries it. A reconcile loop says "keep
  checking until desired is achieved" — inherently retries and
  self-heals.
- **Real-world payoff demonstrated in the demo:** pods crash randomly
  every iteration (simulating real infra failures) and the reconciler
  brings the count back to 3 every single time, with no special
  "recover from crash" code path — recovery *is* just another
  reconcile pass.

## Run it

```bash
python3 reconcile.py
```
