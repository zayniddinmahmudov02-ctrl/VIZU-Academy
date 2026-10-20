import { api } from "@/src/services/api";

const BASE = "/api/v1/admin/notifications";

export interface AdminBroadcast {
  id: string;
  title_de: string;
  title_uz: string;
  message_de: string;
  message_uz: string;
  type: "INFO" | "SUCCESS" | "WARNING" | "ANNOUNCEMENT";
  audience_type: "ALL" | "LEVEL" | "LANGUAGE" | "USER";
  audience_value: string | null;
  audience_student: { id: string; email: string; name: string } | null;
  link_type: "NONE" | "INTERNAL" | "EXTERNAL";
  internal_route: string | null;
  internal_params: Record<string, string> | null;
  external_url: string | null;
  link: { type: string; path?: string; url?: string } | null;
  is_important: boolean;
  status: "DRAFT" | "PUBLISHED" | "INACTIVE" | "ARCHIVED";
  /** status with SCHEDULED for a future publish time */
  state: string;
  publish_at: string | null;
  archived_at: string | null;
  created_at: string;
  editable: boolean;
  recipients: number | null;
  reads: number;
}

export interface BroadcastMeta {
  audiences: string[];
  types: string[];
  levels: string[];
  languages: string[];
  internal_routes: { key: string; group: string; label: string; path: string; params: { name: string; choices: string[] }[] }[];
}

export type BroadcastPayload = Partial<Pick<AdminBroadcast, "title_de" | "title_uz" | "message_de" | "message_uz" | "type" | "audience_type" |
  "audience_value" | "link_type" | "internal_route" | "internal_params" | "external_url" | "is_important">>;

export const getBroadcastMeta = async () => (await api.get<BroadcastMeta>(`${BASE}/meta`)).data;
export const listBroadcasts = async (status: string, page: number) =>
  (await api.get<{ items: AdminBroadcast[]; total: number; page: number; page_size: number }>(BASE, { params: { status: status || undefined, page } })).data;
export const createBroadcast = async (data: BroadcastPayload) => (await api.post<AdminBroadcast>(BASE, data)).data;
export const updateBroadcast = async (id: string, data: BroadcastPayload) => (await api.put<AdminBroadcast>(`${BASE}/${id}`, data)).data;
export const publishBroadcast = async (id: string, publishAt: string | null, confirm: boolean) =>
  (await api.post<AdminBroadcast>(`${BASE}/${id}/publish`, { publish_at: publishAt, confirm })).data;
export const deactivateBroadcast = async (id: string) => (await api.post<AdminBroadcast>(`${BASE}/${id}/deactivate`)).data;
export const archiveBroadcast = async (id: string) => (await api.post<AdminBroadcast>(`${BASE}/${id}/archive`)).data;
export const resolveStudent = async (q: string) => (await api.get<{ id: string; email: string; name: string }>(`${BASE}/resolve-student`, { params: { q } })).data;
