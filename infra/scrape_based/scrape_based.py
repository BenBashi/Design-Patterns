"""
SCRAPE-BASED (POLLING) PATTERN
================================
Category : Infra / Architectural
Interview tag: "Periodically pull/scrape state from a source at a fixed
                interval, rather than waiting to be pushed updates."

Real-world infra use case in this file
----------------------------------------
This is exactly how Prometheus works: it doesn't wait for services to
push metrics at it — it periodically SCRAPES an HTTP `/metrics` endpoint
on each target on a fixed interval, and stores what it finds.

We simulate:
  - Several "targets" (services) exposing a /metrics endpoint
  - A Scraper that polls each target on a schedule
  - A simple in-memory time-series store
  - A threshold check (poor-man's alerting) run after each scrape

Contrast with event_driven.py (push model) and watcher.py (long-lived
subscription to a stream of changes).
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Simulated scrape targets — in real life these are HTTP endpoints like
# http://service-a:9100/metrics returning Prometheus exposition format.
# ---------------------------------------------------------------------------
class MetricsTarget:
    """A service that exposes metrics for scraping."""

    def __init__(self, name: str, base_cpu: float):
        self.name = name
        self._base_cpu = base_cpu

    def scrape_endpoint(self) -> dict:
        """Simulates an HTTP GET to /metrics. Values fluctuate randomly."""
        cpu_percent = max(0.0, min(100.0, self._base_cpu + random.uniform(-10, 25)))
        return {
            "cpu_percent": round(cpu_percent, 1),
            "memory_mb": round(random.uniform(200, 800), 1),
            "requests_total": random.randint(100, 5000),
        }


# ---------------------------------------------------------------------------
# Time-series store — where scraped samples land, like Prometheus's TSDB.
# ---------------------------------------------------------------------------
@dataclass
class Sample:
    target: str
    metrics: dict
    scraped_at: float = field(default_factory=time.time)


class TimeSeriesStore:
    def __init__(self):
        self._samples: list[Sample] = []

    def record(self, sample: Sample) -> None:
        self._samples.append(sample)

    def latest_for(self, target: str) -> Sample | None:
        matches = [s for s in self._samples if s.target == target]
        return matches[-1] if matches else None

    def history_for(self, target: str) -> list[Sample]:
        return [s for s in self._samples if s.target == target]


# ---------------------------------------------------------------------------
# The Scraper — the core of the pattern: pull on a fixed interval.
# ---------------------------------------------------------------------------
class Scraper:
    def __init__(self, targets: list[MetricsTarget], store: TimeSeriesStore,
                 interval_seconds: float = 1.0, cpu_alert_threshold: float = 90.0):
        self._targets = targets
        self._store = store
        self._interval = interval_seconds
        self._cpu_alert_threshold = cpu_alert_threshold

    def scrape_once(self) -> None:
        """One scrape cycle across all targets — this is what a scheduler
        (cron, a Timer thread, or Prometheus's own scrape loop) calls
        repeatedly, forever, at `interval_seconds` cadence."""
        for target in self._targets:
            metrics = target.scrape_endpoint()
            sample = Sample(target=target.name, metrics=metrics)
            self._store.record(sample)
            print(f"[Scraper] scraped {target.name}: {metrics}")
            self._check_alerts(sample)

    def _check_alerts(self, sample: Sample) -> None:
        cpu = sample.metrics["cpu_percent"]
        if cpu >= self._cpu_alert_threshold:
            print(f"[Scraper] 🚨 ALERT: {sample.target} CPU at {cpu}% "
                  f"(threshold {self._cpu_alert_threshold}%)")

    def run(self, cycles: int) -> None:
        """Runs a fixed number of scrape cycles, sleeping `interval` between
        each — in production this loop runs forever (or via a cron/
        Timer-based scheduler) rather than a bounded `cycles` count."""
        for i in range(cycles):
            print(f"\n--- Scrape cycle {i + 1}/{cycles} ---")
            self.scrape_once()
            if i < cycles - 1:
                time.sleep(self._interval)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
def _demo():
    random.seed(42)  # deterministic-ish output for readability

    targets = [
        MetricsTarget("service-a", base_cpu=40),
        MetricsTarget("service-b", base_cpu=75),  # will occasionally alert
    ]
    store = TimeSeriesStore()
    scraper = Scraper(targets, store, interval_seconds=0.2, cpu_alert_threshold=90.0)

    scraper.run(cycles=3)

    print("\n=== Query the store after scraping ===")
    for target in targets:
        latest = store.latest_for(target.name)
        print(f"Latest sample for {target.name}: {latest.metrics}")
        print(f"Total samples collected for {target.name}: {len(store.history_for(target.name))}")


if __name__ == "__main__":
    _demo()
