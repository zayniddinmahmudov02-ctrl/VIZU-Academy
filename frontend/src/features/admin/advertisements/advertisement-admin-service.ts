import { api } from "@/src/services/api";
import { ensureArray } from "@/lib/ensure-array";

const BASE = "/api/v1/admin/advertisements";

export type AdvertisementLinkType = "EXTERNAL" | "INTERNAL";

/** A student page an internal link may point to — the server's whitelist
 * (backend app/services/student_routes.py), never a free path. */
export interface InternalRoute {
  key: string;
  group: string;
  label: string;
  path: string;
  params: { name: string; choices: string[] }[];
}

export async function listInternalRoutes(): Promise<InternalRoute[]> {
  const response = await api.get<InternalRoute[]>(`${BASE}/internal-routes`);
  return ensureArray<InternalRoute>(response.data);
}

export interface AdminAdvertisement {
  id: string;
  title: string;
  description: string | null;
  image_url: string | null;
  link_type: AdvertisementLinkType;
  target_url: string | null;
  internal_route: string | null;
  internal_params: Record<string, string> | null;
  /** resolved student page of an internal link */
  internal_path: string | null;
  /** false: the chosen student page no longer exists — students get the fallback page */
  link_valid: boolean;
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

/** Exactly the backend's AdvertisementCreate contract
 * (backend/app/schemas/advertisement.py). Never send form state directly —
 * build this with the manager's payload mapper. */
export interface CreateAdvertisementPayload {
  title: string;
  /** Optional — null when empty. */
  description: string | null;
  /** The stored upload path ("/uploads/images/...") or an https URL — never the preview URL. */
  image_url: string | null;
  link_type: AdvertisementLinkType;
  /** EXTERNAL: absolute http(s) URL; INTERNAL: null. */
  target_url: string | null;
  /** INTERNAL: a key from GET internal-routes + its allowed params; EXTERNAL: null. */
  internal_route: string | null;
  internal_params: Record<string, string> | null;
  cta_text: string;
  is_active: boolean;
  /** Integer. */
  priority: number;
  /** ISO 8601 in UTC ("2026-10-02T16:45:00.000Z") or null. */
  starts_at: string | null;
  ends_at: string | null;
}

export type UpdateAdvertisementPayload = Partial<CreateAdvertisementPayload>;

export interface AdvertisementFieldError {
  field: string;
  message: string;
}

/** Reads a failed save: FastAPI's 422 body ({detail: [{loc, msg}]}) or the
 * app's {message} body. Returns per-field errors (if any) and a message. */
export function parseAdvertisementApiError(error: unknown): { status?: number; fieldErrors: AdvertisementFieldError[]; message?: string } {
  const response = (error as { response?: { status?: number; data?: unknown } }).response;
  const data = (response?.data ?? {}) as { detail?: unknown; message?: unknown };
  const fieldErrors: AdvertisementFieldError[] = [];
  const items = Array.isArray(data.detail) ? data.detail : Array.isArray(data.message) ? data.message : [];
  for (const item of items as { loc?: unknown[]; msg?: string }[]) {
    const loc = Array.isArray(item?.loc) ? item.loc.filter((x) => x !== "body") : [];
    fieldErrors.push({
      field: loc.length ? String(loc[loc.length - 1]) : "",
      message: String(item?.msg ?? "").replace(/^Value error, /, ""),
    });
  }
  const message =
    typeof data.message === "string" ? data.message : typeof data.detail === "string" ? data.detail : undefined;
  return { status: response?.status, fieldErrors, message };
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

export async function createAdvertisement(data: CreateAdvertisementPayload): Promise<AdminAdvertisement> {
  const response = await api.post<AdminAdvertisement>(BASE, data);
  return response.data;
}

export async function updateAdvertisement(id: string, data: UpdateAdvertisementPayload): Promise<AdminAdvertisement> {
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
