import type { LmsLevelSale, LmsLevelSummary } from "./types";

export type LevelStatus = "ACTIVE" | "LOCKED" | "COMING_SOON" | "PURCHASE_REQUIRED" | "EXPIRED";

/** The state shown on a course card, derived only from what the backend says about the student's access
 * (`sale` of GET /lms/levels): not released -> COMING_SOON; owned / staff -> ACTIVE; bought before but the access period is over
 * -> EXPIRED (owner 2026-11-25: show why, offer to renew); released but no ACTIVE package sells it -> LOCKED; otherwise a purchase
 * opens it (lesson 1 stays free). Presentation only — every lesson is checked again. */
export function levelStatus(level: Pick<LmsLevelSummary, "sale">): LevelStatus {
  const sale = level.sale;
  if (!sale) return "ACTIVE";
  if (sale.coming_soon) return "COMING_SOON";
  if (sale.owned) return "ACTIVE";
  if (sale.expired_at) return "EXPIRED";
  if (sale.sales_closed || !sale.sales_enabled) return "LOCKED";
  return "PURCHASE_REQUIRED";
}

export const STATUS_TONE: Record<LevelStatus, string> = {
  ACTIVE: "bg-success/15 text-success",
  LOCKED: "bg-surface-hover text-text-muted",
  COMING_SOON: "bg-surface-hover text-text-muted",
  PURCHASE_REQUIRED: "bg-accent-blue/10 text-accent-blue",
  EXPIRED: "bg-amber-500/15 text-amber-700 dark:text-amber-300",
};

/** "28.11.2026" in Tashkent time (the school's calendar), for access dates. */
export function accessDate(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return new Intl.DateTimeFormat("de-DE", { day: "2-digit", month: "2-digit", year: "numeric", timeZone: "Asia/Tashkent" }).format(d);
}

/** Where "renew" leads: the level's own offer when it is on sale, else the purchase page (the student picks a package there). */
export function renewHref(sale: Pick<LmsLevelSale, "offer"> | undefined): string {
  return sale?.offer?.purchasable ? `/angebote?offer=${encodeURIComponent(sale.offer.code)}` : "/angebote";
}
