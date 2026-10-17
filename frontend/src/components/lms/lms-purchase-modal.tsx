"use client";

import Link from "next/link";
import { BookOpen, Check, CreditCard, Lock, Package, X } from "lucide-react";

import { useLmsLevel } from "@/features/lms/hooks/use-lms";
import type { LmsSaleOffer } from "@/features/lms/types";
import { useTranslation } from "@/lib/i18n/use-translation";

function price(t: (k: string, v?: Record<string, string | number>) => string, n: number | null) {
  return n == null ? "—" : t("lms.som", { n: n.toLocaleString("ru-RU").replace(/ /g, " ") });
}

/** Purchase sheet for a level. Every price / package / free-lesson number
 * comes from the backend (GET /lms/levels/{level} -> sale, configured in
 * Admin -> Angebote); "buy" opens the existing Angebote checkout — the
 * lessons open only after the server has approved the payment. */
export default function LmsPurchaseModal({ level, open, onClose }: { level: string; open: boolean; onClose: () => void }) {
  const { t } = useTranslation();
  const { data } = useLmsLevel(open ? level : "");
  if (!open) return null;
  const sale = data?.sale;
  const offer = sale?.offer;
  const free = sale?.free_lessons ?? 0;
  const total = data?.lessons_target ?? 0;

  const buyHref = (o: LmsSaleOffer) => `/angebote?offer=${encodeURIComponent(o.code)}`;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-0 sm:items-center sm:p-4" role="dialog" aria-modal="true" onClick={onClose}>
      <div className="max-h-[92vh] w-full max-w-lg overflow-y-auto rounded-t-3xl bg-surface-card p-6 shadow-[var(--shadow-lg)] ring-1 ring-surface-border sm:rounded-3xl"
           onClick={(e) => e.stopPropagation()} data-testid="lms-purchase-modal">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">{t("lms.level")} {level}</p>
            <h2 className="text-xl font-bold text-text-primary">{t("lms.buyTitle", { level })}</h2>
          </div>
          <button onClick={onClose} aria-label="Close" className="rounded-lg p-1.5 text-text-muted hover:bg-surface-hover"><X size={18} /></button>
        </div>

        {!data ? (
          <div className="flex justify-center py-10"><div className="h-8 w-8 animate-spin rounded-full border-[3px] border-surface-border border-t-accent-blue" /></div>
        ) : sale?.coming_soon ? (
          <p className="rounded-xl bg-surface-hover p-4 text-sm text-text-secondary"><Lock size={14} className="mr-1 inline" />{t("lms.comingSoonHint")}</p>
        ) : sale?.owned ? (
          <p className="rounded-xl bg-success/10 p-4 text-sm font-medium text-success"><Check size={14} className="mr-1 inline" />{t("lms.buyOwned")}</p>
        ) : (
          <div className="space-y-5">
            <ul className="space-y-2 text-sm text-text-secondary">
              <li className="flex items-center gap-2"><BookOpen size={15} className="text-accent-blue" /> {t("lms.buyLessons", { n: total })}</li>
              {free > 0 && <li className="flex items-center gap-2"><Check size={15} className="text-success" /> {t("lms.buyFree")}</li>}
              <li className="flex items-center gap-2"><Check size={15} className="text-success" />
                {free > 0 && total > free ? t("lms.buyUnlocks", { from: free + 1, to: total }) : t("lms.buyUnlocksAll")}</li>
            </ul>

            {offer?.purchasable ? (
              <div className="rounded-2xl bg-accent-blue/5 p-4 ring-1 ring-accent-blue/20" data-testid="lms-purchase-offer">
                <div className="flex items-end gap-2">
                  <span className="text-2xl font-extrabold text-text-primary">{price(t, offer.sale_price)}</span>
                  {offer.original_price && offer.original_price !== offer.sale_price && (
                    <span className="pb-0.5 text-sm text-text-muted line-through">{price(t, offer.original_price)}</span>
                  )}
                </div>
                <Link href={buyHref(offer)} className="mt-3 flex items-center justify-center gap-2 rounded-xl bg-accent-blue px-5 py-3 text-sm font-semibold text-white hover:opacity-90"
                      data-testid="lms-purchase-buy">
                  <CreditCard size={16} /> {t("lms.buyCourse")}
                </Link>
              </div>
            ) : (
              <p className="rounded-xl bg-surface-hover p-4 text-sm text-text-secondary">{t("lms.buyNotForSale")}</p>
            )}

            {sale && sale.packages.length > 0 && (
              <div className="space-y-2">
                <p className="text-sm font-bold text-text-primary">{t("lms.buyPackagesTitle")}</p>
                {sale.packages.map((p) => (
                  <div key={p.code} className="flex items-center gap-3 rounded-2xl p-3 ring-1 ring-surface-border" data-testid="lms-purchase-package">
                    <Package size={18} className="shrink-0 text-accent-blue" />
                    <div className="min-w-0 flex-1">
                      <p className="font-semibold text-text-primary">{p.label} · {price(t, p.sale_price)}</p>
                      <p className="text-xs text-text-muted">
                        {t("lms.buyPackageLevels", { levels: p.levels.map((lv) => (p.available_levels.includes(lv) ? lv : `${lv} (${t("lms.comingSoon")})`)).join(", ") })}
                      </p>
                    </div>
                    <Link href={buyHref(p)} className="rounded-xl px-3 py-2 text-xs font-semibold text-accent-blue ring-1 ring-accent-blue/30 hover:bg-accent-blue/10">
                      {t("lms.buyPackage")}
                    </Link>
                  </div>
                ))}
              </div>
            )}

            <div className="space-y-1 rounded-xl bg-surface-hover/60 p-3 text-xs text-text-secondary">
              <p>{t("lms.buyPayment")}</p>
              <p>{t("lms.buyAfter")}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
