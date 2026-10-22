import { api } from "@/src/services/api";

const BASE = "/api/v1/admin/page-management";

export type ManagedPageStatus = "active" | "removed" | "hidden" | "archived";
export type ManagedPageType = "SYSTEM_PAGE" | "ADMIN_PAGE" | "LMS_PAGE" | "CUSTOM_PAGE";

export interface ManagedPage {
  page_id: string;
  name: string;
  route: string;
  module: string;
  page_type: ManagedPageType;
  status: ManagedPageStatus;
  navigation_enabled: boolean;
  navigation_visible: boolean;
  is_hidden: boolean;
  is_archived: boolean;
  allowed_roles: string[];
  in_navigation: boolean;
  component: string;
  related_data: { name: string; exists: boolean }[];
  related_data_exists: boolean;
  can_delete: boolean;
  delete_block_reason: string;
  protected: boolean;
  reason: string | null;
  updated_at: string | null;
  updated_by: { id: string; name: string } | null;
}

export interface ManagedPageAudit {
  id: string;
  route: string;
  action: string;
  previous_state: Record<string, boolean>;
  new_state: Record<string, boolean>;
  reason: string | null;
  actor: { id: string; name: string } | null;
  created_at: string;
}

export async function listManagedPages(filters: {
  q?: string;
  module?: string;
  status?: ManagedPageStatus | "";
  route?: string;
} = {}): Promise<ManagedPage[]> {
  return (await api.get<ManagedPage[]>(`${BASE}/pages`, { params: filters })).data;
}

export async function getManagedPageNavigation(): Promise<Record<string, boolean>> {
  return (await api.get<Record<string, boolean>>(`${BASE}/navigation`)).data;
}

export async function getManagedPageDetails(pageId: string): Promise<ManagedPage> {
  return (await api.get<ManagedPage>(`${BASE}/pages/${encodeURIComponent(pageId)}`)).data;
}

export async function setManagedPageNavigation(pageId: string, enabled: boolean, reason?: string): Promise<void> {
  await api.patch(`${BASE}/pages/${encodeURIComponent(pageId)}/navigation`, { enabled, reason });
}

export async function setManagedPageVisibility(pageId: string, hidden: boolean, reason?: string): Promise<void> {
  await api.patch(`${BASE}/pages/${encodeURIComponent(pageId)}/visibility`, { enabled: hidden, reason });
}

export async function archiveManagedPage(pageId: string, reason?: string): Promise<void> {
  await api.post(`${BASE}/pages/${encodeURIComponent(pageId)}/archive`, { reason });
}

export async function restoreManagedPage(pageId: string, reason?: string): Promise<void> {
  await api.post(`${BASE}/pages/${encodeURIComponent(pageId)}/restore`, { reason });
}

export async function getManagedPageHistory(pageId: string): Promise<ManagedPageAudit[]> {
  return (await api.get<ManagedPageAudit[]>(`${BASE}/pages/${encodeURIComponent(pageId)}/history`)).data;
}
