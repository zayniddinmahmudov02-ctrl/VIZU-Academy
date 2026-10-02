"use client";

import { motion, useReducedMotion } from "framer-motion";
import { Check, Gift, Lock, Sparkles } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import type { Offer } from "../types";

export type OfferState = "available" | "owned" | "pending" | "blocked" | "inactive";

const numberFmt = new Intl.NumberFormat("de-DE");

export function formatSom(value: number): string {
  return numberFmt.format(value);
}

/** Old price struck through + big sale price. Used by the Angebote cards and
 * the course cards, so a price is rendered the same way everywhere. */
export function OfferPrice({ offer, size = "lg" }: { offer: Offer; size?: "lg" | "md" }) {
  const { t } = useTranslation();
  if (!offer.active || offer.salePrice == null) {
    return <p className="text-sm font-semibold text-text-muted">{t("angebote.notAvailable")}</p>;
  }
  return (
    <div className="flex flex-wrap items-baseline gap-x-2.5 gap-y-0.5">
      {offer.originalPrice != null && offer.originalPrice > offer.salePrice && (
        <span className={`${size === "lg" ? "text-base" : "text-sm"} font-medium text-text-muted line-through decoration-orange-500/70 decoration-2`}>
          {formatSom(offer.originalPrice)} {t("angebote.currency")}
        </span>
      )}
      <span className={`${size === "lg" ? "text-4xl" : "text-2xl"} font-extrabold tracking-tight text-accent-blue`}>
        {formatSom(offer.salePrice)}
        <span className={`ml-1 ${size === "lg" ? "text-base" : "text-sm"} font-bold`}>{t("angebote.currency")}</span>
      </span>
    </div>
  );
}

export function OfferBadges({ offer }: { offer: Offer }) {
  const { t } = useTranslation();
  return (
    <div className="flex flex-wrap gap-1.5">
      {offer.active && offer.discountPercent != null && (
        <span className="rounded-full bg-orange-500 px-2.5 py-1 text-[11px] font-extrabold uppercase tracking-wide text-white shadow-sm">
          {t("angebote.discountBadge", { percent: offer.discountPercent })}
        </span>
      )}
      {offer.active && (
        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/12 px-2.5 py-1 text-[11px] font-bold text-emerald-600 ring-1 ring-emerald-500/25 dark:text-emerald-400">
          <Gift size={11} />
          {t("angebote.freeLessonBadge")}
        </span>
      )}
    </div>
  );
}

interface Props {
  offer: Offer;
  state: OfferState;
  highlighted?: boolean;
  compact?: boolean;
  onBuy: () => void;
}

/** One Angebote offer. Packages are the large cards, single levels the
 * compact ones. B2 / C1 (inactive) render "Hozircha aktiv emas" with a
 * disabled button; the backend rejects such an order anyway (409). */
export default function OfferCard({ offer, state, highlighted = false, compact = false, onBuy }: Props) {
  const { t } = useTranslation();
  const reduce = useReducedMotion();
  const inactive = state === "inactive";

  const button = {
    available: { label: t("angebote.buy"), disabled: false },
    owned: { label: t("angebote.owned"), disabled: true },
    pending: { label: t("angebote.pending"), disabled: true },
    blocked: { label: t("angebote.buy"), disabled: true },
    inactive: { label: t("angebote.inactive"), disabled: true },
  }[state];

  return (
    <motion.div
      initial={reduce ? { opacity: 0 } : { opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      data-offer={offer.code}
      className={`relative flex h-full flex-col overflow-hidden rounded-card bg-surface-card shadow-[var(--shadow-md)] ring-1 transition-shadow hover:shadow-[var(--shadow-lg)] ${
        highlighted ? "ring-2 ring-orange-400" : "ring-surface-border"
      } ${inactive ? "opacity-75" : ""} ${compact ? "p-5" : "p-6 sm:p-7"}`}
    >
      {highlighted && (
        <span className="absolute right-4 top-4 inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-orange-500 to-amber-400 px-3 py-1 text-[11px] font-extrabold uppercase tracking-wide text-white shadow">
          <Sparkles size={12} />
          {t("angebote.bestValue")}
        </span>
      )}

      <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-text-muted">
        {offer.kind === "PACKAGE" ? t("angebote.packageKicker") : t("angebote.levelKicker")}
      </p>
      <h3 className={`mt-1 font-extrabold tracking-tight text-text-primary ${compact ? "text-2xl" : "text-3xl"}`}>{offer.label}</h3>

      {offer.kind === "PACKAGE" && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {offer.levels.map((level) => (
            <span key={level} className="rounded-lg bg-accent-blue/10 px-2.5 py-1 text-xs font-bold text-accent-blue">
              {level}
            </span>
          ))}
        </div>
      )}

      <div className="mt-4">
        <OfferBadges offer={offer} />
      </div>

      <div className="mt-4">
        {inactive ? (
          <p className="flex items-center gap-1.5 text-sm font-semibold text-text-muted">
            <Lock size={14} />
            {t("angebote.notAvailable")}
          </p>
        ) : (
          <OfferPrice offer={offer} size={compact ? "md" : "lg"} />
        )}
      </div>

      {!compact && (
        <ul className="mt-5 flex-1 space-y-2 text-sm text-text-secondary">
          {[
            t("angebote.featureContents", { levels: offer.levels.join(" + ") }),
            t("angebote.featureFree"),
            t("angebote.featureRest"),
          ].map((feature) => (
            <li key={feature} className="flex items-start gap-2">
              <Check size={15} className="mt-0.5 shrink-0 text-accent-blue" />
              {feature}
            </li>
          ))}
        </ul>
      )}
      {compact && <div className="flex-1" />}

      <button
        type="button"
        onClick={onBuy}
        disabled={button.disabled}
        className={`mt-6 w-full rounded-xl py-3 text-sm font-bold transition-all active:scale-[0.98] disabled:cursor-not-allowed motion-reduce:transition-none ${
          state === "owned"
            ? "bg-emerald-500/12 text-emerald-600 dark:text-emerald-400"
            : button.disabled
              ? "bg-surface-hover text-text-muted"
              : highlighted
                ? "bg-orange-500 text-white shadow-md hover:bg-orange-600"
                : "bg-accent-blue text-white shadow-md hover:opacity-90"
        }`}
      >
        {button.label}
      </button>
    </motion.div>
  );
}
