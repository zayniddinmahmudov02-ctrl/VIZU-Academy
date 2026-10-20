import { api } from "@/src/services/api";

export interface MyCertificate {
  id: string; // "c:<certificate id>" | "ml:<attempt id>"
  source: "COURSE" | "VORBEREITUNG" | "VIZU_MULTILEVEL";
  type_label: string;
  level: string | null;
  level_label: string | null;
  certificate_number: string | null;
  issued_at: string | null;
  status: "valid" | "revoked" | "issued" | "available";
  score: number | null;
  course: { id: string; title: string; level: string } | null;
  pdf_available: boolean;
  attempt_id: string | null;
  attempt_number?: number;
}

/** Only the logged-in student's own certificates. */
export async function getMyCertificates(): Promise<MyCertificate[]> {
  const data = (await api.get<{ items: MyCertificate[] }>("/api/v1/my-certificates")).data;
  return Array.isArray(data?.items) ? data.items : [];
}

export async function fetchMyCertificatePdf(itemId: string): Promise<Blob> {
  return (await api.get(`/api/v1/my-certificates/${encodeURIComponent(itemId)}/pdf`, { responseType: "blob" })).data as Blob;
}
