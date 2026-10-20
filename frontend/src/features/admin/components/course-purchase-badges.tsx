"use client";

import { Clock, ShoppingBag } from "lucide-react";

import type { CoursePurchaseItem } from "@/features/admin/types/user.types";

export function formatPurchaseDate(value: string | null): string {
  return value ? new Date(value).toLocaleDateString("de-DE") : "—";
}

/** "Kurs sotib olgan" — only APPROVED course orders reach `purchases`
 * (backend purchases.py). Pending orders are shown as a separate, muted
 * hint and never as a purchase. */
export function CoursePurchaseBadges({
  purchases,
  pendingOrders = 0,
  showDate = false,
}: {
  purchases: CoursePurchaseItem[];
  pendingOrders?: number;
  showDate?: boolean;
}) {
  if (purchases.length === 0 && pendingOrders === 0) return null;
  return (
    <div className="flex flex-wrap items-center gap-1">
      {purchases.map((p) => (
        <span
          key={p.order_id}
          title={`Kurs gekauft: ${p.label} (${p.levels.join(", ")}) · bestätigt am ${formatPurchaseDate(p.purchased_at)} · ${p.amount.toLocaleString("de-DE")} ${p.currency}`}
          className="inline-flex items-center gap-1 rounded-full bg-[var(--admin-accent)]/15 px-2 py-0.5 text-[10px] font-semibold text-[var(--admin-accent)]"
        >
          <ShoppingBag size={10} />
          Kurs {p.label}
          {showDate && <span className="font-normal opacity-80">· {formatPurchaseDate(p.purchased_at)}</span>}
        </span>
      ))}
      {pendingOrders > 0 && (
        <span
          title="Bestellung wartet auf Bestätigung — zählt nicht als Kauf"
          className="inline-flex items-center gap-1 rounded-full bg-[var(--admin-warning)]/15 px-2 py-0.5 text-[10px] font-semibold text-[var(--admin-warning)]"
        >
          <Clock size={10} />
          {pendingOrders} offen
        </span>
      )}
    </div>
  );
}
