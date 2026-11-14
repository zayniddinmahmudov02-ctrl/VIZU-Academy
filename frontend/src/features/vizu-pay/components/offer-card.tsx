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
  // not sold (inactive, not priced or not approved for sale): no price is advertised
  if (!offer.purchasable || offer.salePrice == null) {
    return <p className="text-sm font-semibold text-text-muted">{t("lms.comingSoon")}</p>;
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
      {offer.purchasable && offer.discountPercent != null && (
        <span className="rounded-full bg-orange-500 px-2.5 py-1 text-[11px] font-extrabold uppercase tracking-wide text-white shadow-sm">
          {t("angebote.discountBadge", { percent: offer.discountPercent })}
        </span>
      )}
      {offer.purchasable && (
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

/** Access term from the server (days): whole months as months, otherwise days. */
export function durationLabel(t: (k: string, v?: Record<string, string | number>) => string, days: number | null): string | null {
  if (!days) return null;
  if (days % 30 === 0) return days === 30 ? t("angebote.durationMonth") : t("angebote.durationMonths", { months: days / 30 });
  if (days === 365) return t("angebote.durationMonths", { months: 12 });
  return t("angebote.durationDays", { days });
}

/** Levels of a package students cannot open yet ("Tez orada", e.g. B2 / C1 in A1–C1). */
export function laterLevels(offer: Offer): string[] {
  return offer.levels.filter((level) => !offer.availableLevels.includes(level));
}

/** One package. Bundles are the large cards, single levels the compact ones. A COMING_SOON package shows
 * "Tez orada" / "Keyinroq ochiladi" — no price, no duration, no buy button; the backend refuses such an order (409). */
export default function OfferCard({ offer, state, highlighted = false, compact = false, onBuy }: Props) {
  const { t, language } = useTranslation();
  const reduce = useReducedMotion();
  const inactive = state === "inactive";
  const later = laterLevels(offer);
  const duration = durationLabel(t, offer.durationDays);
  const description = offer.description[language] ?? offer.description.de ?? null;

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
        {offer.kind === "PACKAGE" ? t("angebote.bundle") : t("angebote.individualCourse")}
      </p>
      <h3 className={`mt-1 font-extrabold tracking-tight text-text-primary ${compact ? "text-2xl" : "text-3xl"}`}>
        {offer.levels.length > 1 ? `${offer.levels[0]}–${offer.levels[offer.levels.length - 1]}` : offer.label}
      </h3>

      {offer.kind === "PACKAGE" && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {offer.levels.map((level) =>
            offer.availableLevels.includes(level) ? (
              <span key={level} className="rounded-lg bg-accent-blue/10 px-2.5 py-1 text-xs font-bold text-accent-blue">
                {level}
              </span>
            ) : (
              // in the package, opens for its buyers once the level is released — no new payment
              <span key={level} className="rounded-lg bg-surface-hover px-2.5 py-1 text-xs font-bold text-text-muted" title={t("angebote.comingSoonHint")}>
                {t("angebote.levelLater", { level })}
              </span>
            ),
          )}
        </div>
      )}

      {!inactive && (
        <div className="mt-4">
          <OfferBadges offer={offer} />
        </div>
      )}

      <div className="mt-4">
        {inactive ? (
          <div data-testid="offer-coming-soon">
            <p className="flex items-center gap-1.5 text-sm font-bold text-text-secondary">
              <Lock size={14} />
              {t("angebote.comingSoon")}
            </p>
            <p className="mt-0.5 text-xs text-text-muted">{t("angebote.comingSoonHint")}</p>
          </div>
        ) : (
          <>
            <OfferPrice offer={offer} size={compact ? "md" : "lg"} />
            {duration && <p className="mt-1 text-xs font-semibold text-text-secondary" data-testid="offer-duration">{duration}</p>}
          </>
        )}
      </div>

      {description && <p className="mt-3 text-sm text-text-secondary">{description}</p>}

      {!inactive && later.length > 0 && (
        <p className="mt-3 rounded-xl bg-warning/10 px-3 py-2 text-xs font-medium text-warning ring-1 ring-warning/20" data-testid="offer-later-note">
          {t("angebote.a1c1Short")}
        </p>
      )}

      {!compact && !inactive && (
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
      {(compact || inactive) && <div className="flex-1" />}

      {inactive ? null : (
        <button
          type="button"
          onClick={onBuy}
          disabled={button.disabled}
          data-testid="offer-buy"
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
      )}
    </motion.div>
  );
}
