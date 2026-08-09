"""
FACADE PATTERN
==================
Category : Backend / Structural
Interview tag: "Provide a unified, simplified interface to a set of
                interfaces in a subsystem, hiding its complexity."

Real-world backend use case in this file
-----------------------------------------
An e-commerce "PlaceOrder" flow. Under the hood, placing an order touches
FOUR independent subsystems: Inventory, Payment, Shipping, and
Notifications. Each subsystem has its own quirky API. Client code
(e.g. an HTTP handler) shouldn't need to know all of that — it should just
call `OrderFacade.place_order(...)`.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Complex subsystems (each has its own independent API / responsibility)
# ---------------------------------------------------------------------------
class InventoryService:
    def __init__(self):
        self._stock = {"sku-123": 5, "sku-999": 0}

    def check_stock(self, sku: str, qty: int) -> bool:
        available = self._stock.get(sku, 0)
        print(f"[Inventory] checking stock for {sku}: have {available}, need {qty}")
        return available >= qty

    def reserve(self, sku: str, qty: int) -> None:
        self._stock[sku] -= qty
        print(f"[Inventory] reserved {qty}x {sku}, remaining {self._stock[sku]}")


class PaymentGateway:
    def charge(self, card_token: str, amount_cents: int) -> str:
        print(f"[Payment] charging {amount_cents / 100:.2f} to card {card_token}")
        # pretend we call out to Stripe/Adyen/etc.
        transaction_id = "txn_abc123"
        print(f"[Payment] success, transaction_id={transaction_id}")
        return transaction_id


class ShippingService:
    def schedule_shipment(self, address: str, sku: str, qty: int) -> str:
        print(f"[Shipping] scheduling shipment of {qty}x {sku} to {address}")
        tracking_id = "trk_789xyz"
        print(f"[Shipping] tracking_id={tracking_id}")
        return tracking_id


class NotificationService:
    def send_order_confirmation(self, email: str, tracking_id: str) -> None:
        print(f"[Notification] emailing {email}: your order shipped! track: {tracking_id}")


# ---------------------------------------------------------------------------
# The Facade: one simple method, hides four subsystems and their ordering,
# error handling, and coordination logic.
# ---------------------------------------------------------------------------
@dataclass
class OrderRequest:
    sku: str
    qty: int
    card_token: str
    amount_cents: int
    shipping_address: str
    customer_email: str


class OrderFacade:
    """Unified entry point for placing an order.

    Client code (e.g. a FastAPI/Flask route handler) only needs to know
    about THIS class. It has no idea Inventory, Payment, Shipping, and
    Notifications even exist as separate services.
    """

    def __init__(self):
        self._inventory = InventoryService()
        self._payment = PaymentGateway()
        self._shipping = ShippingService()
        self._notifications = NotificationService()

    def place_order(self, request: OrderRequest) -> dict:
        print(f"\n--- Placing order for {request.sku} x{request.qty} ---")

        if not self._inventory.check_stock(request.sku, request.qty):
            raise RuntimeError(f"Out of stock: {request.sku}")

        self._inventory.reserve(request.sku, request.qty)
        transaction_id = self._payment.charge(request.card_token, request.amount_cents)
        tracking_id = self._shipping.schedule_shipment(
            request.shipping_address, request.sku, request.qty
        )
        self._notifications.send_order_confirmation(request.customer_email, tracking_id)

        return {
            "status": "confirmed",
            "transaction_id": transaction_id,
            "tracking_id": tracking_id,
        }


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
def _demo():
    facade = OrderFacade()

    # Happy path — client code stays trivially simple.
    result = facade.place_order(
        OrderRequest(
            sku="sku-123",
            qty=2,
            card_token="tok_visa",
            amount_cents=4999,
            shipping_address="1 Infinite Loop, Cupertino, CA",
            customer_email="ben@example.com",
        )
    )
    print("\nResult:", result)

    # Failure path — out of stock, facade raises before touching payment.
    print("\n--- Attempting an order that will fail (out of stock) ---")
    try:
        facade.place_order(
            OrderRequest(
                sku="sku-999",
                qty=1,
                card_token="tok_visa",
                amount_cents=999,
                shipping_address="1 Infinite Loop, Cupertino, CA",
                customer_email="ben@example.com",
            )
        )
    except RuntimeError as e:
        print("Order failed as expected:", e)


if __name__ == "__main__":
    _demo()
