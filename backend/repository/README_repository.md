# Repository Pattern

**Category:** Backend / Structural (Data Access Layer)
**File:** `repository.py`

## Intent

Mediate between the domain/business logic layer and the data storage
layer. The repository exposes a collection-like interface
(`get`, `add`, `delete`, `list`) so business logic can work with domain
objects without knowing or caring whether they're stored in Postgres,
Mongo, an in-memory dict, or a REST API.

## When to use it

- Any service layer that needs to be **unit-testable without a real
  database** (swap in an in-memory repository)
- Decoupling business logic from a specific ORM/database technology
- Centralizing query logic so it's not duplicated across the codebase
- Preparing for a future storage migration (e.g. Postgres → DynamoDB)
  without touching business logic

## How it works (this file)

- `User` — a plain domain entity, no persistence awareness.
- `UserRepository(ABC)` — the abstract contract:
  `get_by_id`, `get_by_email`, `add`, `delete`, `list_active`.
- `InMemoryUserRepository` — stores users in a dict. Ideal for tests.
- `SqlUserRepository` — simulates a SQL-backed implementation (prints the
  SQL it "would" run). In real code this is where SQLAlchemy/psycopg2
  live.
- `UserService` — business logic (`register`, `deactivate`,
  `active_users`). It depends **only on `UserRepository`**, injected via
  the constructor — never on a concrete class.

The demo runs the exact same `UserService` logic against both repository
implementations to prove the business logic doesn't change.

## Key interview talking points

- **Dependency Inversion Principle in action:** `UserService` depends on
  an abstraction (`UserRepository`), not a concrete implementation. This
  is the "D" in SOLID applied directly.
- **Why not just use the ORM directly everywhere?** Without a repository,
  ORM query code (`session.query(User).filter(...)`) leaks into business
  logic and controllers, making it hard to test and hard to change ORMs.
- **Repository vs. DAO (Data Access Object):** similar idea, but DAO
  typically maps 1:1 to a table/query set, while Repository models a
  collection of domain objects and can aggregate/hide multiple data
  sources behind one interface.
- **Repository vs. Active Record:** Active Record (e.g. Django models)
  bakes persistence methods (`.save()`) directly into the domain object.
  Repository keeps the domain object pure/persistence-ignorant, and
  externalizes the persistence logic — a cleaner separation but more
  boilerplate.
- **Testing payoff:** in the demo, swapping `InMemoryUserRepository` for
  `SqlUserRepository` required changing exactly one line, and
  `UserService`'s code needed zero changes.

## Run it

```bash
python3 repository.py
```
