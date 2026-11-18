"use client";

import { useState } from "react";
import { Dialog } from "@base-ui/react/dialog";
import { Check, CheckCircle2, Clock3, Copy, Crown, Infinity as InfinityIcon, Loader2, Ticket, UploadCloud, X } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { apiCode, createMlOrder, getMlQuote, mlErrorKey, redeemMlPromo } from "../services/multilevel-premium-service";
import type { MlQuote, MlStatus } from "../services/multilevel-premium-service";

// mirrors the server (vizu_pay/service.py MAX_PROOF_SIZE_BYTES, ALLOWED_PROOF_EXTENSIONS) — the server checks the content again
const MAX_BYTES = 10 * 1024 * 1024;
const RECEIPT_TYPES = [".jpg", ".jpeg", ".png", ".pdf"];

export const som = (value: number) => String(value).replace(/\B(?=(\d{3})+(?!\d))/g, " ");

type Step = "intro" | "promo" | "pay" | "sent" | "redeemed";

interface Props {
  open: boolean;
  status: MlStatus | undefined;
  initialStep?: "intro" | "promo";
  onClose: () => void;
  /** after a payment request or a redeemed code: reload status + exam list */
  onChanged: () => void;
}

export default function MultilevelPremiumModal(props: Props) {
  // remount per opening: every opening starts clean
  return props.open ? <PremiumDialog key={props.initialStep ?? "intro"} {...props} /> : null;
}

const INPUT = "w-full rounded-xl border border-surface-border bg-surface-hover p-3 text-sm text-text-primary outline-none focus:border-accent-blue/60";

function PremiumDialog({ status, initialStep = "intro", onClose, onChanged }: Props) {
  const { t } = useTranslation();
  const [step, setStep] = useState<Step>(initialStep);
  const [code, setCode] = useState("");
  const [quote, setQuote] = useState<MlQuote | null>(null);
  const [appliedPromo, setAppliedPromo] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [noReceipt, setNoReceipt] = useState(false);
  const [paidDate, setPaidDate] = useState("");
  const [paidTime, setPaidTime] = useState("");
  const [note, setNote] = useState("");

  const product = status?.product;
  const price = product?.price ?? 0;
  const amount = appliedPromo && quote ? quote.final_amount : price;
  const card = status?.cards?.[0];
  const canBuy = !!status && !status.entitled && !status.staff && !status.pending_order && !status.blocked && !!product?.purchasable;

  async function checkPromo() {
    if (!code.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const q = await getMlQuote(code.trim());
      setQuote(q);
      if (q.promo_error) setError(t(mlErrorKey(q.promo_error)));
    } catch (err) {
      setQuote(null);
      setError(t(mlErrorKey(apiCode(err))));
    } finally {
      setBusy(false);
    }
  }

  async function redeem() {
    setBusy(true);
    setError(null);
    try {
      await redeemMlPromo(code.trim());
      setStep("redeemed");
      onChanged();
    } catch (err) {
      setError(t(mlErrorKey(apiCode(err))));
    } finally {
      setBusy(false);
    }
  }

  function pickFile(next: File | null) {
    setError(null);
    if (!next) return setFile(null);
    const ext = next.name.slice(next.name.lastIndexOf(".")).toLowerCase();
    if (!RECEIPT_TYPES.includes(ext)) {
      setFile(null);
      return setError(t("mlPremium.fileType"));
    }
    if (next.size > MAX_BYTES) {
      setFile(null);
      return setError(t("mlPremium.fileTooLarge"));
    }
    setFile(next);
  }

  async function submit() {
    setError(null);
    if (!noReceipt && !file) return setError(t("mlPremium.errRECEIPT_REQUIRED"));
    if (noReceipt && (!paidDate || !paidTime)) return setError(t("mlPremium.errPAID_AT_REQUIRED"));
    if ((paidDate && !paidTime) || (!paidDate && paidTime)) return setError(t("mlPremium.errPAID_AT_REQUIRED"));
    setBusy(true);
    try {
      await createMlOrder({ promoCode: appliedPromo ?? undefined, noReceipt, receipt: noReceipt ? null : file, paidDate, paidTime, note });
      setStep("sent");
      onChanged();
    } catch (err) {
      setError(t(mlErrorKey(apiCode(err))));
    } finally {
      setBusy(false);
    }
  }

  async function copyCard() {
    if (!card) return;
    try {
      await navigator.clipboard.writeText(card.number.replace(/\s/g, ""));
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard blocked: the number stays visible to copy by hand */
    }
  }

  return (
    <Dialog.Root open onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Backdrop className="fixed inset-0 z-[60] bg-black/50 backdrop-blur-sm" />
        <Dialog.Popup className="fixed left-1/2 top-1/2 z-[61] max-h-[90vh] w-[92vw] max-w-md -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-card bg-surface-card p-5 shadow-[var(--shadow-lg)] ring-1 ring-surface-border outline-none sm:p-6"
          data-testid="ml-premium-modal" data-step={step}>
          <div className="mb-4 flex items-start justify-between gap-3">
            <Dialog.Title className="flex items-center gap-2 text-base font-extrabold tracking-tight text-text-primary sm:text-lg">
              <Crown size={20} className="shrink-0 text-amber-500" /> {t("mlPremium.title")}
            </Dialog.Title>
            <Dialog.Close className="rounded-lg p-1 text-text-muted transition-colors hover:bg-surface-hover hover:text-text-primary" aria-label={t("mlPremium.close")}>
              <X size={18} />
            </Dialog.Close>
          </div>

          {step === "intro" && (
            <div className="space-y-4">
              <p className="text-sm text-text-secondary">{t("mlPremium.subtitle")}</p>
              <ul className="space-y-2 text-sm" data-testid="ml-features">
                {[1, 2, 3, 4, 5].map((n) => (
                  <li key={n} className="flex items-center gap-2 text-text-primary"><CheckCircle2 size={16} className="shrink-0 text-success" />{t(`mlPremium.feature${n}`)}</li>
                ))}
              </ul>
              <div className="flex flex-wrap items-end justify-between gap-2 rounded-xl bg-amber-500/10 px-4 py-3 ring-1 ring-amber-500/30">
                <p className="text-2xl font-extrabold text-text-primary" data-testid="ml-price">{t("mlPremium.price", { price: som(price) })}</p>
                <p className="flex items-center gap-1 text-xs font-semibold text-amber-600 dark:text-amber-400"><InfinityIcon size={14} />{t("mlPremium.unlimited")}</p>
              </div>
              {status && status.tests.available < status.tests.total && (
                <p className="text-xs text-text-muted" data-testid="ml-tests-ready">{t("mlPremium.testsReady", { available: status.tests.available, total: status.tests.total })}</p>
              )}
              <StatusNotice status={status} />
              {canBuy && (
                <div className="grid gap-2 sm:grid-cols-2">
                  <button type="button" onClick={() => setStep("pay")} data-testid="ml-buy"
                    className="rounded-xl bg-accent-blue px-4 py-3 text-sm font-bold text-white transition hover:brightness-110">
                    {status?.last_rejected ? t("mlPremium.retry") : t("mlPremium.buy")}
                  </button>
                  <button type="button" onClick={() => setStep("promo")} data-testid="ml-enter-promo"
                    className="flex items-center justify-center gap-1.5 rounded-xl border border-surface-border px-4 py-3 text-sm font-bold text-text-primary transition hover:bg-surface-hover">
                    <Ticket size={15} />{t("mlPremium.enterPromo")}
                  </button>
                </div>
              )}
            </div>
          )}

          {step === "promo" && (
            <div className="space-y-3">
              <label className="block text-xs font-semibold text-text-secondary" htmlFor="ml-promo">{t("mlPremium.promoTitle")}</label>
              <div className="flex gap-2">
                <input id="ml-promo" value={code} autoComplete="off" maxLength={40} placeholder={t("mlPremium.promoPlaceholder")} data-testid="ml-promo-input"
                  onChange={(e) => { setCode(e.target.value.toUpperCase()); setQuote(null); setError(null); }} className={INPUT} />
                <button type="button" onClick={() => void checkPromo()} disabled={!code.trim() || busy} data-testid="ml-promo-check"
                  className="shrink-0 rounded-xl border border-surface-border px-3 text-xs font-semibold text-text-secondary transition-colors hover:bg-surface-hover disabled:opacity-40">
                  {busy ? <Loader2 size={14} className="animate-spin" /> : t("mlPremium.promoCheck")}
                </button>
              </div>
              {quote && !quote.promo_error && (
                <div className="space-y-2 rounded-xl bg-success/10 p-3 text-sm text-text-primary ring-1 ring-success/25" data-testid="ml-promo-result">
                  {quote.free ? (
                    <>
                      <p>{t("mlPremium.promoFree")}</p>
                      <button type="button" onClick={() => void redeem()} disabled={busy} data-testid="ml-promo-unlock"
                        className="w-full rounded-xl bg-success px-4 py-2.5 text-sm font-bold text-white transition hover:brightness-110 disabled:opacity-50">
                        {t("mlPremium.promoUnlock")}
                      </button>
                    </>
                  ) : (
                    <>
                      <p>{t("mlPremium.promoDiscount", { discount: som(quote.promo_discount), final: som(quote.final_amount) })}</p>
                      <button type="button" onClick={() => { setAppliedPromo(code.trim()); setStep("pay"); }} data-testid="ml-promo-continue"
                        className="w-full rounded-xl bg-accent-blue px-4 py-2.5 text-sm font-bold text-white transition hover:brightness-110">
                        {t("mlPremium.promoContinue")}
                      </button>
                    </>
                  )}
                </div>
              )}
              <BackButton onClick={() => { setStep("intro"); setError(null); }} />
            </div>
          )}

          {step === "pay" && (
            <div className="space-y-4">
              <h4 className="text-sm font-bold text-text-primary">{t("mlPremium.payTitle")}</h4>
              {card && (
                <div className="flex items-center justify-between gap-2 rounded-xl bg-surface-hover px-3.5 py-2.5">
                  <div className="min-w-0">
                    <p className="text-[11px] font-semibold uppercase tracking-wide text-text-muted">{t("mlPremium.cardLabel")}</p>
                    <p className="font-mono text-base font-bold tracking-wide text-text-primary" data-testid="ml-card-number">
                      {card.number.replace(/\s/g, "").replace(/(\d{4})(?=\d)/g, "$1 ")}
                    </p>
                  </div>
                  <button type="button" onClick={() => void copyCard()} data-testid="ml-card-copy"
                    className="flex shrink-0 items-center gap-1.5 rounded-lg border border-surface-border px-3 py-1.5 text-xs font-semibold text-text-secondary transition-colors hover:bg-surface-card">
                    {copied ? <Check size={13} className="text-success" /> : <Copy size={13} />}
                    {copied ? t("mlPremium.copied") : t("mlPremium.copy")}
                  </button>
                </div>
              )}
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-text-secondary" htmlFor="ml-amount">{t("mlPremium.amount")}</label>
                {/* shown, never sent: the server sets the amount */}
                <input id="ml-amount" readOnly value={t("mlPremium.price", { price: som(amount) })} data-testid="ml-amount" className={`${INPUT} font-bold`} />
                {appliedPromo && <p className="mt-1 text-xs text-success">{t("mlPremium.promoApplied", { code: appliedPromo })}</p>}
              </div>
              <p className="rounded-xl bg-accent-blue/10 p-3 text-xs leading-relaxed text-text-secondary" data-testid="ml-instruction">
                {t("mlPremium.instruction", { price: som(amount) })}
              </p>

              {!noReceipt && (
                <div>
                  <p className="mb-1.5 block text-xs font-semibold text-text-secondary">{t("mlPremium.receipt")}</p>
                  <label className="flex cursor-pointer items-center gap-2 rounded-xl border border-dashed border-surface-border px-3 py-3 text-sm text-text-secondary transition hover:bg-surface-hover">
                    <UploadCloud size={18} className="shrink-0" />
                    <span className="min-w-0 truncate">{file ? file.name : t("mlPremium.receiptChoose")}</span>
                    <input type="file" className="sr-only" accept=".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf" data-testid="ml-receipt"
                      onChange={(e) => pickFile(e.target.files?.[0] ?? null)} />
                  </label>
                </div>
              )}
              <label className="flex items-start gap-2 text-sm text-text-primary">
                <input type="checkbox" className="mt-1" checked={noReceipt} data-testid="ml-no-receipt"
                  onChange={(e) => { setNoReceipt(e.target.checked); setError(null); if (e.target.checked) setFile(null); }} />
                <span>{t("mlPremium.noReceipt")}{noReceipt && <span className="block text-xs text-text-muted">{t("mlPremium.noReceiptHint")}</span>}</span>
              </label>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-text-secondary" htmlFor="ml-paid-date">{t("mlPremium.paidDate")}{noReceipt && " *"}</label>
                  <input id="ml-paid-date" type="date" value={paidDate} onChange={(e) => setPaidDate(e.target.value)} required={noReceipt}
                    data-testid="ml-paid-date" className={INPUT} />
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-text-secondary" htmlFor="ml-paid-time">{t("mlPremium.paidTime")}{noReceipt && " *"}</label>
                  <input id="ml-paid-time" type="time" value={paidTime} onChange={(e) => setPaidTime(e.target.value)} required={noReceipt}
                    data-testid="ml-paid-time" className={INPUT} />
                </div>
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-text-secondary" htmlFor="ml-note">{t("mlPremium.note")}</label>
                <textarea id="ml-note" rows={2} maxLength={1000} value={note} onChange={(e) => setNote(e.target.value)} data-testid="ml-note" className={INPUT} />
              </div>
              <button type="button" onClick={() => void submit()} disabled={busy} data-testid="ml-submit"
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-accent-blue px-4 py-3 text-sm font-bold text-white transition hover:brightness-110 disabled:opacity-50">
                {busy && <Loader2 size={15} className="animate-spin" />}
                {busy ? t("mlPremium.submitting") : t("mlPremium.submit")}
              </button>
              <BackButton onClick={() => { setStep(appliedPromo ? "promo" : "intro"); setError(null); }} />
            </div>
          )}

          {step === "sent" && (
            <div className="space-y-3 text-center" data-testid="ml-sent">
              <Clock3 size={36} className="mx-auto text-warning" />
              <p className="font-bold text-warning">{t("mlPremium.pendingTitle")}</p>
              <p className="text-sm text-text-secondary">{t("mlPremium.sent")}</p>
              <CloseButton onClick={onClose} />
            </div>
          )}

          {step === "redeemed" && (
            <div className="space-y-3 text-center" data-testid="ml-redeemed">
              <CheckCircle2 size={36} className="mx-auto text-success" />
              <p className="font-bold text-success">{t("mlPremium.redeemed")}</p>
              <CloseButton onClick={onClose} />
            </div>
          )}

          {error && <p className="mt-3 rounded-xl bg-danger/10 px-3 py-2 text-sm text-danger" role="alert" data-testid="ml-error">{error}</p>}
        </Dialog.Popup>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

/** pending / active / rejected / blocked / not for sale — the same words as the page banner */
export function StatusNotice({ status }: { status: MlStatus | undefined }) {
  const { t } = useTranslation();
  if (!status) return null;
  if (status.staff) return <Notice tone="success" testId="ml-status-staff" title={t("mlPremium.activeTitle")} body={t("mlPremium.staffBody")} />;
  if (status.entitled) return <Notice tone="success" testId="ml-status-active" title={t("mlPremium.activeTitle")} body={t("mlPremium.activeBody")} />;
  if (status.pending_order) return <Notice tone="warning" testId="ml-status-pending" title={t("mlPremium.pendingTitle")} body={t("mlPremium.pendingBody")} />;
  if (status.blocked) return <Notice tone="danger" testId="ml-status-blocked" title={t("mlPremium.blocked")} />;
  if (!status.product.purchasable) return <Notice tone="muted" testId="ml-status-closed" title={t("mlPremium.notForSale")} />;
  if (status.last_rejected) {
    return <Notice tone="danger" testId="ml-status-rejected" title={t("mlPremium.rejectedTitle")}
      body={status.last_rejected.reason ? t("mlPremium.rejectedReason", { reason: status.last_rejected.reason }) : undefined} />;
  }
  return null;
}

const TONES = {
  success: "bg-success/10 text-success ring-success/25",
  warning: "bg-warning/10 text-warning ring-warning/25",
  danger: "bg-danger/10 text-danger ring-danger/25",
  muted: "bg-surface-hover text-text-secondary ring-surface-border",
};

function Notice({ tone, title, body, testId }: { tone: keyof typeof TONES; title: string; body?: string; testId: string }) {
  return (
    <div className={`rounded-xl px-4 py-3 text-sm ring-1 ${TONES[tone]}`} data-testid={testId}>
      <p className="font-bold">{title}</p>
      {body && <p className="mt-0.5 text-text-secondary">{body}</p>}
    </div>
  );
}

function BackButton({ onClick }: { onClick: () => void }) {
  const { t } = useTranslation();
  return <button type="button" onClick={onClick} className="w-full rounded-xl px-4 py-2 text-sm font-semibold text-text-secondary hover:bg-surface-hover">{t("mlPremium.back")}</button>;
}

function CloseButton({ onClick }: { onClick: () => void }) {
  const { t } = useTranslation();
  return <button type="button" onClick={onClick} className="w-full rounded-xl bg-surface-hover px-4 py-2.5 text-sm font-bold text-text-primary">{t("mlPremium.close")}</button>;
}
