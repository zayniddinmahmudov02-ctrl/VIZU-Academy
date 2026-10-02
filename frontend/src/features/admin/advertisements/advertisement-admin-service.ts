import { api } from "@/src/services/api";
import { ensureArray } from "@/lib/ensure-array";

const BASE = "/api/v1/admin/advertisements";

export interface AdminAdvertisement {
  id: string;
  title: string;
  description: string | null;
  image_url: string | null;
  target_url: string;
  cta_text: string;
  is_active: boolean;
  priority: number;
  starts_at: string | null;
  ends_at: string | null;
  created_at: string;
  updated_at: string;
  impressions: number;
  clicks: number;
  ctr: number;
  /** The one advertisement students currently see on the dashboard. */
  is_current: boolean;
}

export interface AdvertisementPayload {
  title: string;
  description: string | null;
  image_url: string | null;
  target_url: string;
  cta_text: string;
  is_active: boolean;
  priority: number;
  starts_at: string | null;
  ends_at: string | null;
}

export interface AdvertisementAnalytics {
  advertisement_id: string;
  impressions: number;
  clicks: number;
  ctr: number;
  impressions_today: number;
  clicks_today: number;
  impressions_week: number;
  clicks_week: number;
  series: { date: string; impressions: number; clicks: number }[];
}

export async function listAdvertisements(): Promise<AdminAdvertisement[]> {
  const response = await api.get<AdminAdvertisement[]>(BASE);
  return ensureArray<AdminAdvertisement>(response.data);
}

export async function createAdvertisement(data: AdvertisementPayload): Promise<AdminAdvertisement> {
  const response = await api.post<AdminAdvertisement>(BASE, data);
  return response.data;
}

export async function updateAdvertisement(id: string, data: Partial<AdvertisementPayload>): Promise<AdminAdvertisement> {
  const response = await api.put<AdminAdvertisement>(`${BASE}/${id}`, data);
  return response.data;
}

export async function setAdvertisementActive(id: string, active: boolean): Promise<AdminAdvertisement> {
  const response = await api.post<AdminAdvertisement>(`${BASE}/${id}/${active ? "activate" : "deactivate"}`);
  return response.data;
}

export async function deleteAdvertisement(id: string): Promise<void> {
  await api.delete(`${BASE}/${id}`);
}

export async function getAdvertisementAnalytics(id: string): Promise<AdvertisementAnalytics> {
  const response = await api.get<AdvertisementAnalytics>(`${BASE}/${id}/analytics`);
  return response.data;
}
