import { api } from "@/src/services/api";
import { API_URL } from "@/constants/api";

/** What the student dashboard receives — no analytics, no destination URL. */
export interface ActiveAdvertisement {
  id: string;
  title: string;
  description: string | null;
  image_url: string | null;
  cta_text: string;
  /** Tracking redirect: registers the click, then 302s to the real link. */
  click_path: string;
}

export async function getActiveAdvertisement(): Promise<ActiveAdvertisement | null> {
  const response = await api.get<ActiveAdvertisement | null>("/api/v1/advertisements/active");
  return response.data ?? null;
}

export async function trackAdvertisementImpression(id: string): Promise<void> {
  await api.post(`/api/v1/advertisements/${id}/impression`);
}

export function advertisementClickUrl(ad: ActiveAdvertisement): string {
  return `${API_URL}${ad.click_path}`;
}
