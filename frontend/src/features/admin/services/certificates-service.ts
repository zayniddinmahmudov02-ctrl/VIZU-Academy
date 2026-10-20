import { api } from "@/src/services/api";
import { ensureArray } from "@/lib/ensure-array";
import { createCrudApi } from "../lib/crud-api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type {
  Certificate,
  CertificateCreate,
  CertificateHolderListResponse,
  CertificateUpdate,
  UserCertificateEntry,
} from "../types/certificate.types";

export const certificatesApi = createCrudApi<Certificate, CertificateCreate, CertificateUpdate>(
  ADMIN_ENDPOINTS.certificates,
);

export async function listCertificateHolders(params: {
  page?: number;
  page_size?: number;
}): Promise<CertificateHolderListResponse> {
  const response = await api.get<CertificateHolderListResponse>(`${ADMIN_ENDPOINTS.certificates}/by-user`, {
    params,
  });
  return response.data;
}

export async function getUserCertificateProfile(userId: string): Promise<UserCertificateEntry[]> {
  const response = await api.get<UserCertificateEntry[]>(`${ADMIN_ENDPOINTS.certificates}/by-user/${userId}`);
  return ensureArray<UserCertificateEntry>(response.data);
}

// ---- unified view: certificate rows + VIZU-Multilevel exam certificates (GET /admin/zertifikate)

export type ZertifikatSource = "COURSE" | "VORBEREITUNG" | "VIZU_MULTILEVEL";
export type ZertifikatStatus = "valid" | "revoked" | "issued" | "available";

export interface ZertifikatItem {
  id: string; // "c:<certificate id>" | "ml:<attempt id>"
  source: ZertifikatSource;
  type_label: string;
  level: string | null;
  level_label: string | null;
  certificate_number: string | null;
  issued_at: string | null;
  status: ZertifikatStatus;
  score: number | null;
  course: { id: string; title: string; level: string } | null;
  user?: { id: string; name: string; email: string; username: string } | null;
  pdf_available: boolean;
  attempt_id: string | null;
  attempt_number?: number;
}

export interface ZertifikatFilters {
  q?: string;
  level?: string;
  source?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
  user_id?: string;
  page?: number;
  page_size?: number;
}

export interface ZertifikatList {
  items: ZertifikatItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  stats: { total: number; by_source: Record<string, number>; by_level: Record<string, number> };
}

export async function listZertifikate(filters: ZertifikatFilters): Promise<ZertifikatList> {
  const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== undefined && v !== ""));
  return (await api.get<ZertifikatList>("/api/v1/admin/zertifikate", { params })).data;
}

/** The PDF through the authenticated client (no public file URL). */
export async function fetchZertifikatPdf(itemId: string): Promise<Blob> {
  return (await api.get(`/api/v1/admin/zertifikate/${encodeURIComponent(itemId)}/pdf`, { responseType: "blob" })).data as Blob;
}

// A plain <a href> can't carry the Bearer auth header this backend requires
// (no cookie-based session exists) — the PDF has to be fetched through the
// authenticated axios client and turned into a local blob URL to trigger
// the browser's save dialog.
export async function downloadCertificate(certificateId: string, filename: string): Promise<void> {
  const response = await api.get(`${ADMIN_ENDPOINTS.certificates}/download/${certificateId}`, {
    responseType: "blob",
  });

  const url = URL.createObjectURL(response.data as Blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
