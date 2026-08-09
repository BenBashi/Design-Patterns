# Facade Pattern

**Category:** Backend / Structural
**File:** `facade.py`

## Intent

Provide a single, simplified interface to a complex subsystem made of many
interacting parts. The client talks to the facade; it never has to know
the subsystem's internal classes, their order of invocation, or their
individual APIs.

## When to use it

- Wrapping multiple microservices/SDKs behind one internal API
  (e.g. "PlaceOrder" hides Inventory + Payment + Shipping + Notifications)
- Simplifying a legacy or third-party library with a huge surface area
- Giving each layer of an app (e.g. HTTP handlers) a clean entry point
  into business logic, without leaking implementation details upward
- Decoupling client code from subsystems that may change independently

## How it works (this file)

`facade.py` models an e-commerce checkout: `InventoryService`,
`PaymentGateway`, `ShippingService`, and `NotificationService` are four
independent subsystems, each with its own API and responsibility.

`OrderFacade.place_order(...)` is the single method client code calls. It:

1. Checks and reserves inventory
2. Charges the payment method
3. Schedules shipping
4. Sends a confirmation notification

The client (e.g. an HTTP route handler) only imports `OrderFacade` — it has
zero knowledge that four separate services even exist.

## Key interview talking points

- **Facade vs. Adapter:** Adapter changes an interface to match what the
  client expects (one-to-one wrapper). Facade simplifies/unifies **many**
  interfaces into one, often adding coordination logic (ordering, error
  handling) on top — it's not just a passthrough.
- **Facade does NOT prevent access to subsystems.** Advanced clients can
  still reach `InventoryService` directly if they need fine-grained
  control; the facade is a convenience layer, not a hard boundary.
- **Where it fits in a real backend:** this is essentially what a
  "Service layer" or "Application Service" is in layered architecture —
  it sits between HTTP controllers and domain/infrastructure code.
- **Testability win:** you can unit test `OrderFacade` by mocking the four
  subsystems, and you can unit test each subsystem independently — nice
  separation of concerns.
- **Coordinates failure handling in one place:** notice `place_order`
  raises before charging payment if stock is unavailable — that
  cross-subsystem sequencing logic belongs in the facade, not scattered
  across callers.

## Run it

```bash
python3 facade.py
```
