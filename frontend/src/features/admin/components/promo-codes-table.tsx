"use client";

import { Trash2 } from "lucide-react";

import type { PromoCodeItem } from "../types/vizu-pay";
import { Badge } from "./badges";
import DataTable, { type DataTableColumn } from "./data-table";

function formatDate(value: string | null): string {
  if (!value) return "No expiry";
  return new Intl.DateTimeFormat("de-DE", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(value));
}

interface Props {
  promos: PromoCodeItem[];
  loading: boolean;
  onToggleActive: (promoId: string, isActive: boolean) => void;
  onDelete: (promoId: string) => void;
}

export default function PromoCodesTable({ promos, loading, onToggleActive, onDelete }: Props) {
  const columns: DataTableColumn<PromoCodeItem>[] = [
    {
      key: "code",
      label: "Code",
      render: (promo) => <span className="font-mono text-sm font-semibold text-white">{promo.code}</span>,
    },
    {
      key: "campaign",
      label: "Campaign",
      render: (promo) => <span className="text-sm text-[var(--admin-text-secondary)]">{promo.campaign ?? "—"}</span>,
    },
    {
      key: "discount",
      label: "Discount",
      render: (promo) => (
        <span className="text-sm text-white">
          {promo.discountValue}
          {promo.discountType === "PERCENT" ? "%" : " UZS"}
        </span>
      ),
    },
    {
      key: "usage",
      label: "Usage",
      render: (promo) => (
        <span className="text-sm text-[var(--admin-text-secondary)]">
          {promo.usedCount} / {promo.maxUses ?? "∞"}
        </span>
      ),
    },
    {
      key: "expires",
      label: "Expires",
      render: (promo) => <span className="text-xs text-[var(--admin-text-secondary)]">{formatDate(promo.expiresAt)}</span>,
    },
    {
      key: "status",
      label: "Status",
      render: (promo) => (
        <button type="button" onClick={() => onToggleActive(promo.id, promo.isActive)}>
          <Badge label={promo.isActive ? "Active" : "Inactive"} tone={promo.isActive ? "success" : "neutral"} />
        </button>
      ),
    },
    {
      key: "actions",
      label: "",
      render: (promo) => (
        <button
          type="button"
          onClick={() => onDelete(promo.id)}
          title="Delete (deactivates if already used)"
          className="rounded-lg border border-[#ef4444]/30 p-1.5 text-[#ef4444] transition-colors hover:bg-[#ef4444]/10"
        >
          <Trash2 size={14} />
        </button>
      ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      rows={promos}
      getRowKey={(promo) => promo.id}
      loading={loading}
      emptyLabel="No promo codes yet."
      minWidth="820px"
    />
  );
}
