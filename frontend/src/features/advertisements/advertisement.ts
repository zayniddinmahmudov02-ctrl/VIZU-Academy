import { api } from "@/src/services/api";
import { API_URL } from "@/constants/api";

/** What the student dashboard receives — no analytics, no destination URL. */
export interface ActiveAdvertisement {
  id: string;
  title: string;
  description: string | null;
  image_url: string | null;
  cta_text: string;
  /** EXTERNAL: tracking redirect (registers the click, then 302s to the real
   * link). INTERNAL: POST here reports the click. */
  click_path: string;
  link_type?: "EXTERNAL" | "INTERNAL";
  /** INTERNAL: a whitelisted student page resolved by the server
   * ("/kurse/a1"); a removed page arrives as the safe fallback. */
  internal_path?: string | null;
}

/** In-app path of an internal ad — only a same-site absolute path is used. */
export function advertisementInternalPath(ad: ActiveAdvertisement): string | null {
  const path = ad.link_type === "INTERNAL" ? ad.internal_path : null;
  return path && path.startsWith("/") && !path.startsWith("//") ? path : null;
}

export async function trackAdvertisementClick(id: string): Promise<void> {
  await api.post(`/api/v1/advertisements/${id}/click`);
}

export async function getActiveAdvertisement(): Promise<ActiveAdvertisement | null> {
  const response = await api.get<ActiveAdvertisement | null>("/api/v1/advertisements/active");
  return response.data ?? null;
}

/** Every advertisement currently eligible for the dashboard carousel, in
 * display order (priority first). */
export async function getActiveAdvertisements(): Promise<ActiveAdvertisement[]> {
  const response = await api.get<ActiveAdvertisement[]>("/api/v1/advertisements/active-list");
  return Array.isArray(response.data) ? response.data : [];
}

export async function trackAdvertisementImpression(id: string): Promise<void> {
  await api.post(`/api/v1/advertisements/${id}/impression`);
}

export function advertisementClickUrl(ad: ActiveAdvertisement): string {
  return `${API_URL}${ad.click_path}`;
}
