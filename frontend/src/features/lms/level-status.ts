import type { LmsLevelSummary } from "./types";

export type LevelStatus = "ACTIVE" | "LOCKED" | "COMING_SOON" | "PURCHASE_REQUIRED";

/** The state shown on a course card, derived only from what the backend says about the student's access
 * (`sale` of GET /lms/levels): not released -> COMING_SOON; owned / staff -> ACTIVE; released but no ACTIVE package
 * sells it -> LOCKED; otherwise a purchase opens it (lesson 1 stays free). Presentation only — every lesson is checked again. */
export function levelStatus(level: Pick<LmsLevelSummary, "sale">): LevelStatus {
  const sale = level.sale;
  if (!sale) return "ACTIVE";
  if (sale.coming_soon) return "COMING_SOON";
  if (sale.owned) return "ACTIVE";
  if (sale.sales_closed || !sale.sales_enabled) return "LOCKED";
  return "PURCHASE_REQUIRED";
}

export const STATUS_TONE: Record<LevelStatus, string> = {
  ACTIVE: "bg-success/15 text-success",
  LOCKED: "bg-surface-hover text-text-muted",
  COMING_SOON: "bg-surface-hover text-text-muted",
  PURCHASE_REQUIRED: "bg-accent-blue/10 text-accent-blue",
};
