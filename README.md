# Design Patterns Study Pack (Backend & Infra)

Prepared for the interview prompt:

> We expect a solid theoretical and practical understanding of core
> Design Patterns (Backend & Infra) — Backend: Singleton, Facade,
> Repository, MVC, and core OOP concepts. Infra: Event-driven,
> Scrape-based, Watcher, Reconcile.

Every pattern has a runnable, heavily-commented `.py` file plus a
dedicated `README_*.md` with intent, real-world use cases, and interview
talking points. Each file runs standalone with no dependencies beyond
the Python 3 standard library.

## Structure

```
design-patterns/
├── backend/
│   ├── singleton.py          + README_singleton.md
│   ├── facade.py              + README_facade.md
│   ├── repository.py          + README_repository.md
│   └── mvc.py                 + README_mvc.md
├── infra/
│   ├── event_driven.py        + README_event_driven.md
│   ├── scrape_based.py        + README_scrape_based.md
│   ├── watcher.py             + README_watcher.md
│   └── reconcile.py           + README_reconcile.md
└── oop/
    └── oop_concepts.py        + README_oop_concepts.md
        (inheritance, interfaces, polymorphism, encapsulation, composition)
```

## Run everything

```bash
cd design-patterns
python3 backend/singleton.py
python3 backend/facade.py
python3 backend/repository.py
python3 backend/mvc.py
python3 infra/event_driven.py
python3 infra/scrape_based.py
python3 infra/watcher.py
python3 infra/reconcile.py
python3 oop/oop_concepts.py
```

## The big-picture story for the interview

**Backend patterns** are about organizing code *within* a single
service: Singleton controls instance lifecycle, Facade simplifies a
complex subsystem behind one interface, Repository decouples business
logic from storage, MVC separates data/logic/presentation. OOP concepts
(inheritance, interfaces, polymorphism, encapsulation, composition) are
the vocabulary all of the above are built from.

**Infra patterns** are about how independent systems stay in sync with
reality, and they form a natural progression:

- **Scrape-based (pull):** simplest, self-healing, but latency-bound —
  ask "is anything different?" on a timer.
- **Event-driven (push):** decoupled pub/sub, low-latency, but requires
  reliable delivery and idempotent consumers.
- **Watcher:** a long-lived subscription to one resource's change stream,
  maintaining a local mirror (an "informer" cache) — a middle ground
  that's push-based like events but scoped/stateful like polling.
- **Reconcile:** the convergence loop triggered by a Watcher (or a
  periodic safety-net timer) — level-triggered, idempotent, self-healing.
  This is the actual engine inside every Kubernetes controller: Watcher
  says "something changed," Reconcile decides "what to do about it."

If asked to pick one thing to remember from each domain: backend
patterns are about **decoupling code from its dependencies**; infra
patterns are about **decoupling desired state from actual state, and
detecting drift between them** — one push-based (event/watch), one
pull-based (scrape), converging via reconcile.

## Verification

All nine `.py` files were executed end-to-end; each runs cleanly with no
errors or unhandled exceptions (some print expected/handled errors as
part of their demo, e.g. insufficient funds, out-of-stock, fraud-check
block).
