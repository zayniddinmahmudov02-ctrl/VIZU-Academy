import { api } from "@/src/services/api";
import type { Paged, SupportTicket, SupportTicketSummary } from "@/features/support/support-service";

const BASE = "/api/v1/admin/support";

export interface AdminTicketList extends Paged<SupportTicketSummary> {
  counts: Record<string, number>;
}

export interface TicketFilters {
  status?: string;
  category?: string;
  q?: string;
  date_from?: string;
  date_to?: string;
  assigned?: string;
  page?: number;
}

export const listSupportTickets = async (f: TicketFilters) => {
  const params = Object.fromEntries(Object.entries(f).filter(([, v]) => v !== undefined && v !== ""));
  const data = (await api.get<AdminTicketList>(`${BASE}/tickets`, { params })).data;
  return { ...data, items: Array.isArray(data?.items) ? data.items : [] };
};
export const getSupportTicket = async (id: string) => (await api.get<SupportTicket>(`${BASE}/tickets/${id}`)).data;
export const replySupportTicket = async (id: string, message: string, status: string, requestId: string) =>
  (await api.post<SupportTicket>(`${BASE}/tickets/${id}/reply`, { message, status, request_id: requestId })).data;
export const setSupportStatus = async (id: string, status: string) => (await api.patch<SupportTicket>(`${BASE}/tickets/${id}/status`, { status })).data;
export const assignSupportTicket = async (id: string, assigneeId: string | null) =>
  (await api.patch<SupportTicket>(`${BASE}/tickets/${id}/assign`, { assignee_id: assigneeId })).data;
export const listSupportStaff = async () => (await api.get<{ id: string; name: string | null; role: string }[]>(`${BASE}/staff`)).data;
