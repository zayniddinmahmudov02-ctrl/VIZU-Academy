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
