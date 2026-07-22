"""Payment gateway abstraction for VIZU Pay.

Today only ManualGateway exists: the student uploads a payment screenshot
or PDF and a SUPER_ADMIN reviews it by hand. `SubscriptionOrder.gateway`
and `.gateway_reference` exist so a future automated gateway (Click, Payme,
Stripe) can slot in by implementing PaymentGateway below and registering
itself in GATEWAYS — no other part of the order flow needs to change.

Do not add real Click/Payme/Stripe calls here until credentials and a real
merchant account exist; a stub that pretends to call an external API would
be worse than no integration at all.
"""

from abc import ABC, abstractmethod


class PaymentGateway(ABC):
    """Contract a future automated gateway integration must satisfy."""

    name: str

    @abstractmethod
    def requires_manual_proof(self) -> bool:
        """Whether the student must upload proof for admin review (manual
        flow) vs. the gateway confirming payment itself (automated flow)."""

    @abstractmethod
    def verify(self, order) -> bool:
        """Return True if the order's payment is confirmed by this gateway.
        Manual gateway always defers to admin review (returns False here —
        confirmation happens via the admin approve action, not this call)."""


class ManualGateway(PaymentGateway):
    name = "manual"

    def requires_manual_proof(self) -> bool:
        return True

    def verify(self, order) -> bool:
        return False


GATEWAYS: dict[str, PaymentGateway] = {
    "manual": ManualGateway(),
}


def get_gateway(name: str) -> PaymentGateway:
    return GATEWAYS.get(name, GATEWAYS["manual"])
