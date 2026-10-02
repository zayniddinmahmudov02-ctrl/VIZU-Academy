import type { OfferState } from "./components/offer-card";
import type { Offer, SubscriptionStatus } from "./types";

/** What the viewer can do with an offer. Purely for the UI — the backend
 * re-checks every rule (inactive, already owned, pending, blocked) on
 * POST /vizu-pay/orders. */
export function offerState(offer: Offer, status: SubscriptionStatus | null | undefined): OfferState {
  if (!offer.active || offer.salePrice == null) return "inactive";
  if (status) {
    const owned = status.isPremium || offer.levels.every((level) => status.ownedLevels.includes(level));
    if (owned) return "owned";
    if (status.isBlocked) return "blocked";
    if (status.hasPendingOrder) return "pending";
  }
  return "available";
}
