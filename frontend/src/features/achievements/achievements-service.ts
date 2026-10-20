import { api } from "@/src/services/api";

export type RewardStatus = "AVAILABLE" | "RESERVED" | "USED" | "NONE" | null;

export interface MedalReward {
  type: "ORDER_DISCOUNT";
  value: number;
  offers: string[];
  currency: string;
  /** null while the medal is not earned yet */
  status: RewardStatus;
}

/** One medal as the student sees it (GET /achievements/me) — texts in both
 * languages come from the admin CMS, the component picks the active one. */
export interface Medal {
  id: string;
  key: string;
  category: { key: string; name_de: string; name_uz: string } | null;
  name_de: string;
  name_uz: string;
  description_de: string | null;
  description_uz: string | null;
  icon_preset: string;
  icon_color: string;
  image_url: string | null;
  condition_de: string;
  condition_uz: string;
  earned: boolean;
  awarded_at: string | null;
  reward: MedalReward | null;
}

export interface MyAchievements {
  earned: number;
  total: number;
  items: Medal[];
}

export async function getMyAchievements(): Promise<MyAchievements> {
  const data = (await api.get<MyAchievements>("/api/v1/achievements/me")).data;
  return { earned: data?.earned ?? 0, total: data?.total ?? 0, items: Array.isArray(data?.items) ? data.items : [] };
}

/** Picks the text of the active UI language (de / uz). */
export function localized<T extends object>(item: T, field: string, language: string): string {
  const record = item as Record<string, unknown>;
  const value = record[`${field}_${language === "uz" ? "uz" : "de"}`] ?? record[`${field}_de`];
  return typeof value === "string" ? value : "";
}
