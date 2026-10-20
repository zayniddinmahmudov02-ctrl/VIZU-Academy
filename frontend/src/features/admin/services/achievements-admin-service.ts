import { api } from "@/src/services/api";
import { ensureArray } from "@/lib/ensure-array";

const BASE = "/api/v1/admin/achievements";

export interface AchievementCategory {
  id: string;
  key: string;
  name_de: string;
  name_uz: string;
  order_index: number;
  is_active: boolean;
  achievement_count: number;
}

export interface AdminAchievement {
  id: string;
  key: string;
  category_id: string;
  category: { key: string; name_de: string; name_uz: string } | null;
  name_de: string;
  name_uz: string;
  description_de: string | null;
  description_uz: string | null;
  icon_preset: string;
  icon_color: string;
  image_url: string | null;
  condition_type: string;
  condition_params: Record<string, string | number>;
  condition_de: string;
  condition_uz: string;
  reward_type: "NONE" | "ORDER_DISCOUNT";
  reward_value: number;
  reward_offers: string[];
  reward_combine_with_promo: boolean;
  is_active: boolean;
  order_index: number;
  awarded_count: number;
  reward_counts: Record<string, number>;
}

export interface AchievementMeta {
  conditions: { type: string; label_de: string; label_uz: string; params: string[]; levels: string[] }[];
  icon_presets: string[];
  icon_colors: string[];
  reward_types: string[];
  offers: { code: string; label: string }[];
  max_reward: number;
}

export interface AchievementAward {
  id: string;
  user_id: string;
  email: string;
  name: string;
  awarded_at: string;
  reward_type: string;
  reward_value: number;
  reward_status: string;
  reward_used_at: string | null;
  order: { id: string; plan: string; status: string; final_amount: number } | null;
}

export type AchievementPayload = Partial<Omit<AdminAchievement, "id" | "category" | "condition_de" | "condition_uz" | "awarded_count" | "reward_counts">>;

export const getAchievementMeta = async () => (await api.get<AchievementMeta>(`${BASE}/meta`)).data;
export const listAchievementCategories = async () => ensureArray<AchievementCategory>((await api.get(`${BASE}/categories`)).data);
export const createAchievementCategory = async (data: { key: string; name_de: string; name_uz: string; order_index?: number }) =>
  (await api.post<AchievementCategory>(`${BASE}/categories`, data)).data;
export const listAchievements = async (categoryId?: string) =>
  ensureArray<AdminAchievement>((await api.get(BASE, { params: categoryId ? { category_id: categoryId } : {} })).data);
export const createAchievement = async (data: AchievementPayload) => (await api.post<AdminAchievement>(BASE, data)).data;
export const updateAchievement = async (id: string, data: AchievementPayload) => (await api.put<AdminAchievement>(`${BASE}/${id}`, data)).data;
export const listAchievementAwards = async (id: string) => ensureArray<AchievementAward>((await api.get(`${BASE}/${id}/awards`)).data);
