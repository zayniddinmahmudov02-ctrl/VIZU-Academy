"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Dialog } from "@base-ui/react/dialog";
import { Gift, Medal as MedalLucide, X } from "lucide-react";

import MedalIcon from "@/components/achievements/medal-icon";
import { getMyAchievements, localized, type Medal } from "@/features/achievements/achievements-service";
import { useTranslation } from "@/lib/i18n/use-translation";

const fmt = new Intl.NumberFormat("de-DE");

function RewardText({ medal }: { medal: Medal }) {
  const { t } = useTranslation();
  const r = medal.reward;
  if (!r) return null;
  const status = r.status === "AVAILABLE" ? t("dashboard.achRewardAvailable")
    : r.status === "RESERVED" ? t("dashboard.achRewardReserved")
      : r.status === "USED" ? t("dashboard.achRewardUsed") : null;
  return (
    <div className="rounded-xl bg-success/10 p-3 text-sm text-text-primary">
      <p className="flex items-center gap-1.5 font-semibold"><Gift size={14} className="text-success" aria-hidden="true" /> {t("dashboard.achReward")}</p>
      <p className="mt-0.5">{t("dashboard.achRewardDiscount", { value: fmt.format(r.value), offers: r.offers.join(", ") })}</p>
      {status && <p className="mt-0.5 text-xs text-text-secondary" data-testid="medal-reward-status">{status}</p>}
    </div>
  );
}

/** "Erfolge": earned and open medals (GET /achievements/me — earned ones are
 * awarded by the server only). A click opens the details. */
export default function AchievementsCard() {
  const { t, language } = useTranslation();
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ["achievements", "me"], queryFn: getMyAchievements, staleTime: 30_000 });
  const [open, setOpen] = useState<Medal | null>(null);
  const locale = language === "uz" ? "uz-UZ" : "de-DE";

  return (
    <section className="flex h-full flex-col rounded-card bg-surface-card p-5 shadow-[var(--shadow-card)] ring-1 ring-surface-border" aria-labelledby="ach-title" data-testid="dashboard-achievements">
      <div className="flex items-center gap-2">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/15 text-emerald-500"><MedalLucide size={18} aria-hidden="true" /></span>
        <h2 id="ach-title" className="font-bold text-text-primary">{t("dashboard.achTitle")}</h2>
        {data && data.total > 0 && (
          <span className="ml-auto text-xs font-semibold text-text-muted">{t("dashboard.achEarnedCount", { earned: data.earned, total: data.total })}</span>
        )}
      </div>

      {isLoading ? (
        <div className="mt-4 h-24 animate-pulse rounded-xl bg-surface-hover" aria-busy="true" aria-label={t("dashboard.loading")} />
      ) : isError || !data ? (
        <p className="mt-4 text-sm text-text-secondary">
          {t("dashboard.loadError")}{" "}
          <button type="button" onClick={() => refetch()} className="font-semibold text-accent-blue hover:underline">{t("dashboard.retry")}</button>
        </p>
      ) : data.items.length === 0 ? (
        <p className="mt-4 text-sm text-text-secondary">{t("dashboard.achEmpty")}</p>
      ) : (
        <ul className="mt-4 grid grid-cols-3 gap-3 sm:grid-cols-4 lg:grid-cols-3">
          {data.items.map((m) => {
            const name = localized(m, "name", language);
            return (
              <li key={m.id}>
                <button type="button" onClick={() => setOpen(m)} aria-label={t("dashboard.achDetails", { name })} data-testid="medal" data-earned={m.earned}
                        className="flex w-full flex-col items-center gap-1.5 rounded-xl p-2 text-center transition-colors hover:bg-surface-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-blue">
                  <MedalIcon preset={m.icon_preset} color={m.icon_color} imageUrl={m.image_url} earned={m.earned} size={52} />
                  <span className={`line-clamp-2 text-xs font-semibold ${m.earned ? "text-text-primary" : "text-text-muted"}`}>{name}</span>
                </button>
              </li>
            );
          })}
        </ul>
      )}

      <Dialog.Root open={open !== null} onOpenChange={(o) => !o && setOpen(null)}>
        <Dialog.Portal>
          <Dialog.Backdrop className="fixed inset-0 z-[60] bg-black/50 backdrop-blur-sm" />
          <Dialog.Popup className="fixed left-1/2 top-1/2 z-[61] max-h-[90vh] w-[92vw] max-w-sm -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-card bg-surface-card p-6 shadow-[var(--shadow-lg)] ring-1 ring-surface-border outline-none"
                        data-testid="medal-dialog">
            {open && (
              <div className="flex flex-col items-center gap-3 text-center">
                <Dialog.Close className="ml-auto rounded-lg p-1 text-text-muted hover:bg-surface-hover" aria-label={t("dashboard.achClose")}><X size={18} /></Dialog.Close>
                <MedalIcon preset={open.icon_preset} color={open.icon_color} imageUrl={open.image_url} earned={open.earned} size={96} />
                <div>
                  {open.category && <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">{localized(open.category, "name", language)}</p>}
                  <Dialog.Title className="text-xl font-bold text-text-primary">{localized(open, "name", language)}</Dialog.Title>
                  <p className={`mt-1 text-xs font-semibold ${open.earned ? "text-success" : "text-text-muted"}`}>
                    {open.earned && open.awarded_at
                      ? t("dashboard.achEarnedOn", { date: new Date(open.awarded_at).toLocaleDateString(locale) })
                      : t("dashboard.achLocked")}
                  </p>
                </div>
                {localized(open, "description", language) && <p className="text-sm text-text-secondary">{localized(open, "description", language)}</p>}
                <div className="w-full rounded-xl bg-surface-hover p-3 text-left text-sm">
                  <p className="font-semibold text-text-primary">{t("dashboard.achCondition")}</p>
                  <p className="mt-0.5 text-text-secondary">{localized(open, "condition", language)}</p>
                </div>
                <div className="w-full text-left"><RewardText medal={open} /></div>
              </div>
            )}
          </Dialog.Popup>
        </Dialog.Portal>
      </Dialog.Root>
    </section>
  );
}
