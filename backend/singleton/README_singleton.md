# Singleton Pattern

**Category:** Backend / Creational
**File:** `singleton.py`

## Intent

Ensure a class has exactly one instance, and provide a single global access
point to it. Every caller gets the *same* object.

## When to use it

- App-wide configuration object (load once, read everywhere)
- Database connection pool / client
- Logger
- Cache client wrapper (e.g. single Redis connection)
- Anything expensive to construct that must be shared and consistent

## How it works (this file)

`singleton.py` shows three implementations, from weakest to strongest:

1. **`NaiveSingleton`** — overrides `__new__` to return the same instance.
   Simple but **not thread-safe**: two threads can both pass the `if
   cls._instance is None` check before either sets it, creating two
   instances.
2. **`ThreadSafeSingleton`** — adds **double-checked locking**: check
   without the lock (fast path), then check again *inside* the lock before
   creating. This is the version worth defending in an interview.
3. **`ConfigManager`** via a `@singleton` class decorator — the more
   "Pythonic" approach. Cleaner separation: the decorator handles the
   singleton mechanics, the class just contains business logic.

## Key interview talking points

- **Why it's controversial:** Singleton is often called an anti-pattern
  because it introduces **global mutable state**, which makes unit testing
  harder (hidden dependencies, state leaking between tests) and hides a
  class's true dependencies (violates dependency injection principles).
- **Thread safety** is the #1 follow-up question. Always mention
  double-checked locking or note that Python's GIL makes simple attribute
  reads/writes atomic but not compound check-then-set operations.
- **Alternative in Python:** because modules are cached in `sys.modules`
  after first import, a plain module-level variable (`config = _load()`)
  is *already* a singleton — often simpler and more testable than a class.
- **Testability fix:** prefer **dependency injection** — pass the singleton
  instance into classes that need it (constructor injection) rather than
  having every class reach out and call `ConfigManager()` directly. This
  keeps the singleton but removes hidden coupling.
- **Multiprocessing gotcha:** a Python singleton is only a singleton
  *within one process*. Each worker process (e.g. in Gunicorn with
  multiple workers) gets its own instance — a common surprise in
  interviews about scaling.

## Run it

```bash
python3 singleton.py
```
