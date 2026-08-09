"""
CORE OOP CONCEPTS
==================
Category : Backend / Foundational OOP
Interview tag: "Explain inheritance, interfaces, polymorphism,
                encapsulation, and composition — with real code."

This file covers the five OOP pillars most backend interviews probe:
  1. Inheritance          — "is-a" relationships, shared behavior via a base class
  2. Interfaces            — a contract (ABC / Protocol), no implementation
  3. Polymorphism          — same call, different behavior depending on the object
  4. Encapsulation         — hiding internal state behind a controlled API
  5. Composition           — "has-a" relationships; often preferred over inheritance

Everything below is runnable, with a domain model of payment processing
(a classic backend interview scenario) tying the concepts together.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable


# ---------------------------------------------------------------------------
# 1) INTERFACES — a pure contract, no shared implementation.
#    Python has two idiomatic ways to express this:
#
#    a) ABC (Abstract Base Class) — nominal typing: a class must explicitly
#       inherit from it to "count" as implementing the interface.
#    b) Protocol (structural typing / "duck typing" made static) — a class
#       satisfies the interface just by having the right methods, no
#       inheritance required. This is closer to Go interfaces.
# ---------------------------------------------------------------------------
class PaymentProcessor(ABC):
    """ABC-style interface: subclasses MUST implement `charge`."""

    @abstractmethod
    def charge(self, amount_cents: int) -> str:
        """Returns a transaction id."""
        ...

    @abstractmethod
    def refund(self, transaction_id: str) -> None:
        ...


@runtime_checkable
class Loggable(Protocol):
    """Protocol-style interface: ANY object with a matching `log()` method
    satisfies this, even if it never heard of `Loggable`. No inheritance
    needed — this is structural typing."""

    def log(self, message: str) -> None:
        ...


# ---------------------------------------------------------------------------
# 2) INHERITANCE — "is-a" relationship. Subclasses reuse and extend a base
#    class's behavior. CreditCardProcessor IS-A PaymentProcessor.
# ---------------------------------------------------------------------------
class CreditCardProcessor(PaymentProcessor):
    def __init__(self, gateway_name: str):
        self.gateway_name = gateway_name

    def charge(self, amount_cents: int) -> str:
        txn_id = f"cc_{self.gateway_name}_{amount_cents}"
        print(f"[CreditCardProcessor] charged {amount_cents}c via {self.gateway_name} -> {txn_id}")
        return txn_id

    def refund(self, transaction_id: str) -> None:
        print(f"[CreditCardProcessor] refunded {transaction_id}")


class PayPalProcessor(PaymentProcessor):
    def charge(self, amount_cents: int) -> str:
        txn_id = f"pp_{amount_cents}"
        print(f"[PayPalProcessor] charged {amount_cents}c via PayPal -> {txn_id}")
        return txn_id

    def refund(self, transaction_id: str) -> None:
        print(f"[PayPalProcessor] refunded {transaction_id}")


# Multi-level inheritance: a specialized subclass reusing CreditCardProcessor
class FraudCheckedCreditCardProcessor(CreditCardProcessor):
    """Extends CreditCardProcessor with an extra safety check — reuses
    parent behavior via `super()` instead of duplicating it."""

    def charge(self, amount_cents: int) -> str:
        if amount_cents > 100_000:  # $1000+ triggers a manual review in this toy example
            print("[FraudCheck] amount looks suspicious, flagging for review")
            raise ValueError("Transaction requires manual fraud review")
        return super().charge(amount_cents)  # reuse parent's implementation


# ---------------------------------------------------------------------------
# 3) POLYMORPHISM — code written against the base type works correctly
#    with ANY subclass, without knowing which one it's actually holding.
# ---------------------------------------------------------------------------
def checkout(processor: PaymentProcessor, amount_cents: int) -> str:
    """This function doesn't know or care if `processor` is a credit card,
    PayPal, or fraud-checked variant — it just calls `.charge()`. That's
    polymorphism: one interface, many behaviors."""
    print(f"\n[checkout] processing payment via {type(processor).__name__}")
    return processor.charge(amount_cents)


# ---------------------------------------------------------------------------
# 4) ENCAPSULATION — hide internal state, expose a controlled API.
#    Python doesn't enforce true privacy, but uses convention (`_x`) and
#    name-mangling (`__x`) plus properties to control access.
# ---------------------------------------------------------------------------
class Wallet:
    def __init__(self, owner: str, initial_balance_cents: int = 0):
        self.owner = owner
        self._balance_cents = initial_balance_cents  # "protected" by convention
        self.__pin = "0000"  # "private" via name mangling (becomes _Wallet__pin)

    @property
    def balance_cents(self) -> int:
        """Read-only view of the balance — external code can look but
        can't directly assign `wallet.balance_cents = 999999`."""
        return self._balance_cents

    def deposit(self, amount_cents: int) -> None:
        if amount_cents <= 0:
            raise ValueError("Deposit must be positive")
        self._balance_cents += amount_cents

    def withdraw(self, amount_cents: int) -> None:
        # This is the whole point of encapsulation: the class enforces
        # its own invariants (can't go negative) instead of trusting
        # every caller to check the balance first.
        if amount_cents > self._balance_cents:
            raise ValueError("Insufficient funds")
        self._balance_cents -= amount_cents


# ---------------------------------------------------------------------------
# 5) COMPOSITION — "has-a" relationship. Favored over inheritance when
#    behavior should be assembled from independent, swappable parts
#    rather than baked into a rigid class hierarchy.
#    ("Favor composition over inheritance" — classic OOP design principle.)
# ---------------------------------------------------------------------------
class Notifier:
    def notify(self, message: str) -> None:
        raise NotImplementedError


class EmailNotifier(Notifier):
    def notify(self, message: str) -> None:
        print(f"[EmailNotifier] sending email: {message}")


class SmsNotifier(Notifier):
    def notify(self, message: str) -> None:
        print(f"[SmsNotifier] sending SMS: {message}")


class Order:
    """Order HAS-A Notifier — composed at construction time, swappable
    without touching Order's class hierarchy. Compare this to the
    alternative of making EmailOrder/SmsOrder subclasses, which would
    explode combinatorially if Order also varied by payment type."""

    def __init__(self, order_id: str, notifier: Notifier):
        self.order_id = order_id
        self._notifier = notifier  # composed, not inherited

    def complete(self) -> None:
        print(f"[Order] {self.order_id} completed")
        self._notifier.notify(f"Order {self.order_id} has shipped!")


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
def _demo():
    print("=== Interfaces (ABC) + Inheritance + Polymorphism ===")
    processors: list[PaymentProcessor] = [
        CreditCardProcessor("stripe"),
        PayPalProcessor(),
        FraudCheckedCreditCardProcessor("stripe"),
    ]
    for p in processors:
        checkout(p, 2500)

    print("\n=== Inheritance guarding behavior (fraud check blocks a large charge) ===")
    try:
        checkout(FraudCheckedCreditCardProcessor("stripe"), 500_00)
    except ValueError as e:
        print("Blocked as expected:", e)

    print("\n=== Protocol (structural typing) — no inheritance required ===")
    class ConsoleLogger:  # never inherits from Loggable, still satisfies it
        def log(self, message: str) -> None:
            print(f"[ConsoleLogger] {message}")

    logger = ConsoleLogger()
    print("isinstance(logger, Loggable):", isinstance(logger, Loggable))
    logger.log("Protocols check structure, not ancestry")

    print("\n=== Encapsulation ===")
    wallet = Wallet("ben", initial_balance_cents=1000)
    wallet.deposit(500)
    print("Balance:", wallet.balance_cents)
    try:
        wallet.withdraw(999_999)
    except ValueError as e:
        print("Blocked as expected:", e)
    try:
        wallet.balance_cents = 999_999  # type: ignore  # fails: no setter defined
    except AttributeError as e:
        print("Cannot bypass encapsulation:", e)

    print("\n=== Composition ===")
    order1 = Order("order-1", EmailNotifier())
    order2 = Order("order-2", SmsNotifier())
    order1.complete()
    order2.complete()


if __name__ == "__main__":
    _demo()
