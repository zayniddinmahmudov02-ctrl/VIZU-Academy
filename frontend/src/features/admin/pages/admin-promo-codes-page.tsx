"use client";

import { useState } from "react";
import { Ticket } from "lucide-react";

import { usePromoCodes } from "../hooks/use-admin-vizu-pay";
import AdminModal from "../components/admin-modal";
import PromoCodesTable from "../components/promo-codes-table";

export default function AdminPromoCodesPage() {
  const promos = usePromoCodes();
  const [createOpen, setCreateOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [code, setCode] = useState("");
  const [campaign, setCampaign] = useState("");
  const [discountType, setDiscountType] = useState<"PERCENT" | "FIXED">("PERCENT");
  const [discountValue, setDiscountValue] = useState("10");
  const [maxUses, setMaxUses] = useState("");
  const [expiresAt, setExpiresAt] = useState("");

  function resetForm() {
    setCode("");
    setCampaign("");
    setDiscountType("PERCENT");
    setDiscountValue("10");
    setMaxUses("");
    setExpiresAt("");
    setError(null);
  }

  async function handleCreate() {
    if (!code.trim() || !discountValue) return;
    setError(null);
    try {
      await promos.create({
        code: code.trim(),
        campaign: campaign.trim() || undefined,
        discountType,
        discountValue: Number(discountValue),
        maxUses: maxUses ? Number(maxUses) : undefined,
        expiresAt: expiresAt ? new Date(expiresAt).toISOString() : undefined,
      });
      setCreateOpen(false);
      resetForm();
    } catch (err: any) {
      setError(err?.response?.data?.message ?? "Failed to create promo code.");
    }
  }

  async function handleToggleActive(promoId: string, isActive: boolean) {
    await promos.update(promoId, { isActive: !isActive });
  }

  async function handleDelete(promoId: string) {
    try {
      await promos.remove(promoId);
    } catch {
      // Backend rejects deletion of used codes — deactivate instead.
      await promos.update(promoId, { isActive: false });
    }
  }

  return (
    <div className="space-y-6">
      <div className="admin-glass flex flex-wrap items-center justify-between gap-4 rounded-2xl p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-[var(--admin-primary)] to-[var(--admin-secondary)] text-white">
            <Ticket size={20} />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">Promo Codes</h1>
            <p className="text-xs text-[var(--admin-text-muted)]">{promos.data?.length ?? 0} codes</p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => setCreateOpen(true)}
          className="rounded-xl bg-[var(--admin-primary)] px-4 py-2.5 text-xs font-semibold text-white"
        >
          + New Promo Code
        </button>
      </div>

      <PromoCodesTable
        promos={promos.data ?? []}
        loading={promos.loading}
        onToggleActive={handleToggleActive}
        onDelete={handleDelete}
      />

      <AdminModal open={createOpen} onOpenChange={(open) => { setCreateOpen(open); if (!open) resetForm(); }} title="New Promo Code">
        <div className="space-y-3">
          <input
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase())}
            placeholder="CODE (e.g. WELCOME10)"
            className="w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
          />
          <input
            value={campaign}
            onChange={(e) => setCampaign(e.target.value)}
            placeholder="Campaign name (optional)"
            className="w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
          />
          <div className="flex gap-2">
            <select
              value={discountType}
              onChange={(e) => setDiscountType(e.target.value as "PERCENT" | "FIXED")}
              className="rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
            >
              <option value="PERCENT" className="bg-[#111827]">Percent</option>
              <option value="FIXED" className="bg-[#111827]">Fixed (UZS)</option>
            </select>
            <input
              type="number"
              value={discountValue}
              onChange={(e) => setDiscountValue(e.target.value)}
              placeholder="Value"
              className="w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
            />
          </div>
          <input
            type="number"
            min={1}
            value={maxUses}
            onChange={(e) => setMaxUses(e.target.value)}
            placeholder="Max uses (blank = unlimited)"
            className="w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
          />
          <input
            type="date"
            value={expiresAt}
            onChange={(e) => setExpiresAt(e.target.value)}
            className="w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
          />

          {error && <p className="text-xs text-[#ef4444]">{error}</p>}

          <button
            type="button"
            onClick={handleCreate}
            disabled={!code.trim() || !discountValue}
            className="w-full rounded-xl bg-[var(--admin-primary)] py-2.5 text-sm font-semibold text-white disabled:opacity-40"
          >
            Create Promo Code
          </button>
        </div>
      </AdminModal>
    </div>
  );
}
