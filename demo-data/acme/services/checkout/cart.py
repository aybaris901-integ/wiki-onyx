"""Shopping cart.

Written mostly by Tomas Ruiz (2020-2026). Owned by @priya since 2026-03-02;
see docs/handoffs/tomas-checkout-handover.md for the parts that are not
obvious, especially the price lock.

Why prices are locked at add-to-cart time: Tomas's rule from the 2021 pricing
incident. A customer sees one price, pays that price, even if the catalog
changes while they are in checkout.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CartLine:
    sku: str
    quantity: int
    unit_price_cents: int  # locked when the line was added, see module docstring


@dataclass
class Cart:
    customer_id: str
    lines: list[CartLine] = field(default_factory=list)

    def add(self, sku: str, quantity: int, unit_price_cents: int) -> None:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        for i, line in enumerate(self.lines):
            if line.sku == sku:
                # Keep the original locked price, only bump quantity.
                self.lines[i] = CartLine(sku, line.quantity + quantity, line.unit_price_cents)
                return
        self.lines.append(CartLine(sku, quantity, unit_price_cents))

    def remove(self, sku: str) -> None:
        self.lines = [line for line in self.lines if line.sku != sku]

    def subtotal_cents(self) -> int:
        return sum(line.quantity * line.unit_price_cents for line in self.lines)

    def is_empty(self) -> bool:
        return not self.lines
