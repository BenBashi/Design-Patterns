"""
SINGLETON PATTERN
==================
Category : Backend / Creational
Interview tag: "Ensure a class has only one instance and provide a global
                point of access to it."

Real-world backend use cases
-----------------------------
- Configuration manager (load config.yaml / env vars once, reuse everywhere)
- Database connection pool
- Logger instance
- Cache client (e.g. a single Redis connection wrapper)

This file shows THREE ways to implement it in Python, from naive to
production-grade, plus the anti-pattern pitfalls interviewers like to probe.
"""

from __future__ import annotations

import threading
from typing import Any, Optional


# ---------------------------------------------------------------------------
# 1) Naive Singleton via __new__ override
#    Simple, but NOT thread-safe (two threads can race past the `if` check).
# ---------------------------------------------------------------------------
class NaiveSingleton:
    _instance: Optional["NaiveSingleton"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            print("[NaiveSingleton] creating the one and only instance")
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, value: Any = None):
        # NOTE: __init__ runs every time NaiveSingleton() is called,
        # even though __new__ returns the same object. Guard state
        # initialization or you'll silently overwrite it.
        if not hasattr(self, "_initialized"):
            self.value = value
            self._initialized = True


# ---------------------------------------------------------------------------
# 2) Thread-safe Singleton using double-checked locking.
#    This is the version you want to defend in an interview.
# ---------------------------------------------------------------------------
class ThreadSafeSingleton:
    _instance: Optional["ThreadSafeSingleton"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        # First check without the lock (cheap, avoids locking on the
        # common path once the instance already exists).
        if cls._instance is None:
            with cls._lock:
                # Second check *inside* the lock in case another thread
                # created the instance while we were waiting for it.
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: Optional[dict] = None):
        if not hasattr(self, "_initialized"):
            self.config = config or {}
            self._initialized = True


# ---------------------------------------------------------------------------
# 3) The "Pythonic" way: a module-level singleton, or a decorator.
#    Python modules are already singletons (imported once, cached in
#    sys.modules), so many teams just expose a module-level instance
#    instead of fighting the language with __new__ tricks.
# ---------------------------------------------------------------------------
def singleton(cls):
    """Class decorator that turns any class into a singleton."""
    instances: dict[type, Any] = {}
    lock = threading.Lock()

    def get_instance(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@singleton
class ConfigManager:
    """A realistic backend example: app-wide configuration, loaded once."""

    def __init__(self):
        print("[ConfigManager] loading configuration from disk/env (once!)")
        self.settings = {
            "DB_HOST": "localhost",
            "DB_PORT": 5432,
            "FEATURE_FLAG_NEW_CHECKOUT": True,
        }

    def get(self, key: str) -> Any:
        return self.settings.get(key)

    def set(self, key: str, value: Any) -> None:
        self.settings[key] = value


# ---------------------------------------------------------------------------
# Demo / manual test
# ---------------------------------------------------------------------------
def _demo():
    print("=== Naive Singleton ===")
    a = NaiveSingleton("first")
    b = NaiveSingleton("second")  # value is ignored, same instance returned
    print("a is b:", a is b, "| a.value:", a.value)

    print("\n=== Thread-safe Singleton (with real threads) ===")
    results = []

    def worker():
        instance = ThreadSafeSingleton()
        results.append(id(instance))

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print("All thread instances identical:", len(set(results)) == 1)

    print("\n=== Decorator-based Singleton (ConfigManager) ===")
    cfg1 = ConfigManager()
    cfg2 = ConfigManager()
    print("cfg1 is cfg2:", cfg1 is cfg2)
    cfg1.set("DB_HOST", "prod-db.internal")
    print("cfg2 sees the change too:", cfg2.get("DB_HOST"))


if __name__ == "__main__":
    _demo()
