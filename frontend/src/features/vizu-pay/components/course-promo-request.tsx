"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Loader2, Send, Ticket } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { apiCode } from "../services/multilevel-premium-service";
import { createCourseRequest } from "../services/vizu-pay-service";
import type { Offer } from "../types";

/** "Promo so'rovi": the student asks the admin for a promo for one course / package. The answer (and, if approved, the personal code)
 * shows up in the request list on this page. Only purchasable offers the student does not own yet can be chosen. */
export default function CoursePromoRequest({ offers, ownedLevels }: { offers: Offer[]; ownedLevels: string[] }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const options = offers.filter((o) => o.purchasable && !o.levels.every((lv) => ownedLevels.includes(lv)));
  const [plan, setPlan] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send() {
    if (!plan) return;
    setBusy(true);
    setError(null);
    setDone(false);
    try {
      await createCourseRequest(plan, message.trim());
      setDone(true);
      setMessage("");
      await queryClient.invalidateQueries({ queryKey: ["vizu-pay", "promo-requests"] });
    } catch (err) {
      const code = apiCode(err);
      setError(code === "PROMO_REQUEST_LIMIT" ? t("angebote.courseRequestLimit") : code === "OFFER_ALREADY_OWNED" ? t("angebote.owned")
        : code === "OFFER_NOT_AVAILABLE" ? t("angebote.notAvailable") : t("mlPremium.errGeneric"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="rounded-card bg-surface-card p-5 shadow-[var(--shadow-sm)] ring-1 ring-surface-border" data-testid="course-promo-request">
      <h2 className="mb-1 flex items-center gap-2 text-lg font-bold text-text-primary"><Ticket size={18} className="text-accent-blue" />{t("angebote.courseRequestTitle")}</h2>
      <p className="mb-4 text-sm text-text-secondary">{t("angebote.courseRequestHint")}</p>
      {options.length === 0 ? (
        <p className="text-sm text-text-muted">{t("angebote.courseRequestNone")}</p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-[minmax(0,14rem)_minmax(0,1fr)_auto] sm:items-end">
          <div>
            <label className="mb-1.5 block text-xs font-semibold text-text-secondary" htmlFor="course-request-plan">{t("angebote.courseRequestCourse")}</label>
            <select id="course-request-plan" value={plan} onChange={(e) => { setPlan(e.target.value); setDone(false); }} data-testid="course-request-plan"
              className="w-full rounded-xl border border-surface-border bg-surface-hover p-3 text-sm text-text-primary outline-none focus:border-accent-blue/60">
              <option value="">{t("angebote.courseRequestChoose")}</option>
              {options.map((o) => <option key={o.code} value={o.code}>{o.label}</option>)}
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-semibold text-text-secondary" htmlFor="course-request-message">{t("angebote.courseRequestMessage")}</label>
            <input id="course-request-message" value={message} maxLength={1000} onChange={(e) => setMessage(e.target.value)} data-testid="course-request-message"
              className="w-full rounded-xl border border-surface-border bg-surface-hover p-3 text-sm text-text-primary outline-none focus:border-accent-blue/60" />
          </div>
          <button type="button" onClick={() => void send()} disabled={!plan || busy} data-testid="course-request-send"
            className="flex items-center justify-center gap-1.5 rounded-xl bg-accent-blue px-4 py-3 text-sm font-bold text-white transition hover:brightness-110 disabled:opacity-50">
            {busy ? <Loader2 size={15} className="animate-spin" /> : <Send size={15} />}{t("angebote.courseRequestSend")}
          </button>
        </div>
      )}
      {done && <p className="mt-3 text-sm font-medium text-success" role="status" data-testid="course-request-sent">{t("angebote.courseRequestSent")}</p>}
      {error && <p className="mt-3 text-sm text-danger" role="alert">{error}</p>}
    </section>
  );
}
