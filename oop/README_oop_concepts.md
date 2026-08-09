# Core OOP Concepts

**Category:** Backend / Foundational OOP
**File:** `oop_concepts.py`

## What's covered

A payment-processing domain model ties together the five pillars
interviewers most often probe:

1. **Interfaces** — `PaymentProcessor(ABC)` (nominal typing: must inherit
   to qualify) and `Loggable(Protocol)` (structural typing: qualifies by
   just having the right method, no inheritance needed — like Go).
2. **Inheritance** — `CreditCardProcessor` / `PayPalProcessor` both
   extend `PaymentProcessor`; `FraudCheckedCreditCardProcessor` extends
   `CreditCardProcessor` further and reuses parent logic via `super()`.
3. **Polymorphism** — `checkout(processor, amount)` is written against
   the `PaymentProcessor` interface and works identically regardless of
   which concrete subclass it receives.
4. **Encapsulation** — `Wallet` hides `_balance_cents` behind a read-only
   `@property`, enforces invariants (`withdraw` blocks overdrafts) inside
   the class instead of trusting callers, and hides `__pin` via Python's
   name-mangling.
5. **Composition** — `Order` **has-a** `Notifier` (composed at
   construction), rather than `EmailOrder`/`SmsOrder` subclasses — avoids
   combinatorial explosion if `Order` also varied along other axes.

## Key interview talking points

- **ABC vs. Protocol — know when to use which.** ABC gives you nominal
  typing (explicit `class Foo(MyABC)`) plus the ability to share
  concrete helper methods across implementers. Protocol gives you
  structural typing (`isinstance` checks structure, not ancestry) —
  useful for third-party classes you can't modify to inherit from your
  interface, and closer to how Go's interfaces work.
- **"Favor composition over inheritance"** — the classic GoF guidance.
  Inheritance creates tight coupling to a specific class hierarchy and
  can explode combinatorially (`EmailCreditCardOrder`,
  `SmsCreditCardOrder`, `EmailPayPalOrder`...). Composition lets you mix
  and match independent behaviors (`Notifier` × payment type) freely.
  Use inheritance for genuine **is-a** relationships with shared
  behavior; use composition for **has-a** / "is built from" relationships.
- **Liskov Substitution Principle (the "L" in SOLID):** any subclass
  should be usable anywhere the base class is expected, without breaking
  correctness. `checkout()` in this file only works cleanly *because*
  every `PaymentProcessor` subclass honors that substitutability.
- **Python's "privacy" is convention, not enforcement:** `_balance_cents`
  (single underscore) signals "internal, please don't touch" but isn't
  blocked; `__pin` (double underscore) triggers name-mangling
  (`_Wallet__pin`) which makes accidental external access unlikely but
  still not truly private. Contrast with Java's `private` keyword, which
  the compiler enforces.
- **Why encapsulation matters operationally:** it's not about hiding
  data for its own sake — it's about the class being the **only** place
  that can violate its own invariants. `Wallet.withdraw` guarantees the
  balance never goes negative because there's no other way to mutate it.

## Run it

```bash
python3 oop_concepts.py
```
