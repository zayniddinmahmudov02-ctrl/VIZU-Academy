import { api } from "@/services/api";

export const SUPPORT_CATEGORIES = ["COURSE", "PAYMENT", "MEDIA", "TESTS", "CERTIFICATE", "TECHNICAL", "OTHER"] as const;
export const SUPPORT_STATUSES = ["NEW", "IN_PROGRESS", "WAITING", "ANSWERED", "CLOSED"] as const;
export type SupportCategory = (typeof SUPPORT_CATEGORIES)[number];
export type SupportStatus = (typeof SUPPORT_STATUSES)[number];

export interface SupportTicketSummary {
  id: string;
  number: number;
  display_number: string;
  subject: string;
  category: SupportCategory;
  status: SupportStatus;
  created_at: string;
  updated_at: string;
  last_message_at: string;
  student?: { id: string; email: string | null; name: string | null };
  assigned_to?: { id: string; name: string | null } | null;
}

export interface SupportMessage {
  id: string;
  author_role: "STUDENT" | "STAFF";
  author_name: string | null;
  body: string;
  created_at: string;
}

export interface SupportTicket extends SupportTicketSummary {
  messages: SupportMessage[];
  created?: boolean;
}

export interface Paged<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

/** A fresh id per submit attempt — the server returns the same ticket / message for a repeat. */
export function newRequestId(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export async function listMyTickets(page = 1): Promise<Paged<SupportTicketSummary>> {
  const data = (await api.get<Paged<SupportTicketSummary>>("/api/v1/support/tickets", { params: { page, page_size: 20 } })).data;
  return { ...data, items: Array.isArray(data?.items) ? data.items : [] };
}

export async function createTicket(input: { subject: string; category: string; message: string; request_id: string }): Promise<SupportTicket> {
  return (await api.post<SupportTicket>("/api/v1/support/tickets", input)).data;
}

export async function getMyTicket(id: string): Promise<SupportTicket> {
  return (await api.get<SupportTicket>(`/api/v1/support/tickets/${id}`)).data;
}

export async function sendMyMessage(id: string, message: string, requestId: string): Promise<SupportTicket> {
  return (await api.post<SupportTicket>(`/api/v1/support/tickets/${id}/messages`, { message, request_id: requestId })).data;
}

/** Maps the server's validation codes to translation keys. */
export function supportErrorKey(err: unknown): string {
  const data = (err as { response?: { data?: { message?: unknown; detail?: unknown } } }).response?.data;
  const code = String(data?.message ?? data?.detail ?? "");
  if (code.startsWith("SUBJECT_TOO_SHORT")) return "support.errSubjectShort";
  if (code.startsWith("SUBJECT_TOO_LONG")) return "support.errSubjectLong";
  if (code.startsWith("MESSAGE_TOO_SHORT")) return "support.errMessageShort";
  if (code.startsWith("MESSAGE_TOO_LONG")) return "support.errMessageLong";
  if (code.startsWith("INVALID_CATEGORY")) return "support.errCategory";
  return "support.errGeneric";
}
