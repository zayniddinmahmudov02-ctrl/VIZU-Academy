"use client";

import Link from "next/link";
import { ArrowLeft, BookOpen, Check, CreditCard, Lock, Package, X } from "lucide-react";

import { useLmsLevel } from "@/features/lms/hooks/use-lms";
import type { LmsSaleOffer } from "@/features/lms/types";
import { useTranslation } from "@/lib/i18n/use-translation";

function price(t: (k: string, v?: Record<string, string | number>) => string, n: number | null) {
  return n == null ? "—" : t("lms.som", { n: n.toLocaleString("ru-RU").replace(/ /g, " ") });
}

const buyHref = (code?: string) => (code ? `/angebote?offer=${encodeURIComponent(code)}` : "/angebote");

/** "Buy to continue" sheet for a closed lesson of a level. Every price /
 * package / free-lesson number comes from the backend (GET /lms/levels/{level}
 * -> sale, configured in Admin -> Angebote); "Xarid qilish" opens the
 * purchase page — the lessons open only after the server has approved the
 * payment. `onBack` ("Ortga qaytish") defaults to closing the sheet. */
export default function LmsPurchaseModal({ level, open, onClose, onBack }: {
  level: string; open: boolean; onClose: () => void; onBack?: () => void;
}) {
  const { t } = useTranslation();
  const { data } = useLmsLevel(open ? level : "");
  if (!open) return null;
  const sale = data?.sale;
  const offer = sale?.offer;
  const free = sale?.free_lessons ?? 0;
  const total = data?.lessons_target ?? 0;
  const buyable = !!data && !sale?.coming_soon && !sale?.owned && !!sale?.sales_enabled;
  const options: LmsSaleOffer[] = [...(offer?.purchasable ? [offer] : []), ...(sale?.packages ?? [])];

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-0 sm:items-center sm:p-4" role="dialog" aria-modal="true" onClick={onClose}>
      <div className="max-h-[92vh] w-full max-w-lg overflow-y-auto rounded-t-3xl bg-surface-card p-6 shadow-[var(--shadow-lg)] ring-1 ring-surface-border sm:rounded-3xl"
           onClick={(e) => e.stopPropagation()} data-testid="lms-purchase-modal">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">{t("lms.level")} {level}</p>
            <h2 className="text-xl font-bold text-text-primary" data-testid="lms-purchase-title">
              {buyable || !data ? t("lms.gateTitle") : t("lms.buyTitle", { level })}
            </h2>
          </div>
          <button onClick={onClose} aria-label="Close" className="rounded-lg p-1.5 text-text-muted hover:bg-surface-hover"><X size={18} /></button>
        </div>

        {!data ? (
          <div className="flex justify-center py-10"><div className="h-8 w-8 animate-spin rounded-full border-[3px] border-surface-border border-t-accent-blue" /></div>
        ) : sale?.coming_soon ? (
          <p className="rounded-xl bg-surface-hover p-4 text-sm text-text-secondary"><Lock size={14} className="mr-1 inline" />{t("lms.comingSoonHint")}</p>
        ) : sale?.owned ? (
          <p className="rounded-xl bg-success/10 p-4 text-sm font-medium text-success"><Check size={14} className="mr-1 inline" />{t("lms.buyOwned")}</p>
        ) : !sale?.sales_enabled ? (
          <p className="rounded-xl bg-surface-hover p-4 text-sm text-text-secondary" data-testid="lms-purchase-sales-closed">
            <Lock size={14} className="mr-1 inline" />{t("lms.salesClosedHint")}
          </p>
        ) : (
          <div className="space-y-5">
            <div className="space-y-2 text-sm text-text-secondary" data-testid="lms-purchase-text">
              <p>{t("lms.gateBody")}</p>
              <p className="font-semibold text-text-primary">{t("lms.gateOutro")}</p>
            </div>

            <ul className="space-y-2 text-sm text-text-secondary">
              <li className="flex items-center gap-2"><BookOpen size={15} className="text-accent-blue" /> {t("lms.buyLessons", { n: total })}</li>
              {free > 0 && <li className="flex items-center gap-2"><Check size={15} className="text-success" /> {t("lms.buyFree")}</li>}
              <li className="flex items-center gap-2"><Check size={15} className="text-success" />
                {free > 0 && total > free ? t("lms.buyUnlocks", { from: free + 1, to: total }) : t("lms.buyUnlocksAll")}</li>
            </ul>

            {options.length > 0 && (
              <div className="space-y-2">
                <p className="text-sm font-bold text-text-primary">{t("lms.gateOptions")}</p>
                {options.map((p) => (
                  <Link key={p.code} href={buyHref(p.code)} data-testid={p.kind === "LEVEL" ? "lms-purchase-offer" : "lms-purchase-package"}
                        className="flex items-center gap-3 rounded-2xl p-3 ring-1 ring-surface-border transition-colors hover:bg-accent-blue/5 hover:ring-accent-blue/30">
                    {p.kind === "LEVEL" ? <BookOpen size={18} className="shrink-0 text-accent-blue" /> : <Package size={18} className="shrink-0 text-accent-blue" />}
                    <div className="min-w-0 flex-1">
                      <p className="font-semibold text-text-primary">{p.label}</p>
                      {p.kind !== "LEVEL" && (
                        <p className="text-xs text-text-muted">
                          {t("lms.buyPackageLevels", { levels: p.levels.map((lv) => (p.available_levels.includes(lv) ? lv : `${lv} (${t("lms.comingSoon")})`)).join(", ") })}
                        </p>
                      )}
                    </div>
                    <div className="shrink-0 text-right">
                      <p className="text-sm font-extrabold text-text-primary">{price(t, p.sale_price)}</p>
                      {p.original_price && p.original_price !== p.sale_price && (
                        <p className="text-xs text-text-muted line-through">{price(t, p.original_price)}</p>
                      )}
                    </div>
                  </Link>
                ))}
              </div>
            )}

            <div className="space-y-1 rounded-xl bg-surface-hover/60 p-3 text-xs text-text-secondary">
              <p>{t("lms.buyPayment")}</p>
              <p>{t("lms.buyAfter")}</p>
            </div>
          </div>
        )}

        <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button type="button" onClick={onBack ?? onClose} data-testid="lms-purchase-back"
                  className="inline-flex items-center justify-center gap-2 rounded-xl px-5 py-3 text-sm font-semibold text-text-secondary ring-1 ring-surface-border hover:bg-surface-hover">
            <ArrowLeft size={16} /> {t("lms.gateBack")}
          </button>
          {buyable && (
            <Link href={buyHref(offer?.purchasable ? offer.code : undefined)} data-testid="lms-purchase-buy"
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-accent-blue px-5 py-3 text-sm font-semibold text-white hover:opacity-90">
              <CreditCard size={16} /> {t("lms.gateBuy")}
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
