import { api } from "@/services/api";

import type {
  AdminCertificateItem,
  IssueCertificateInput,
  UpdateCertificateInput,
} from "../types/certificate";

// The certificate router is the only router currently mounted under the
// versioned API prefix (see backend/app/main.py — certificate_router is
// included with prefix=settings.API_V1_PREFIX, which resolves to
// "/api/v1"). Every other admin service in this codebase hits an
// unversioned path, so this base path is intentionally spelled out in
// full rather than following that convention.
const BASE_PATH = "/api/v1/certificates";

interface AdminCertificateApiPayload {
  id: string;
  user_id: string;
  course_id: string;
  certificate_number: string;
  verification_code: string;
  provider: string;
  level: string;
  score: number;
  lesen_score: number;
  hoeren_score: number;
  schreiben_score: number;
  sprechen_score: number;
  pdf_url: string | null;
  qr_code_url: string | null;
  is_valid: boolean;
  issued_at: string;
}

function mapCertificate(raw: AdminCertificateApiPayload): AdminCertificateItem {
  return {
    id: raw.id,
    userId: raw.user_id,
    courseId: raw.course_id,
    certificateNumber: raw.certificate_number,
    verificationCode: raw.verification_code,
    provider: raw.provider,
    level: raw.level,
    score: raw.score,
    lesenScore: raw.lesen_score,
    hoerenScore: raw.hoeren_score,
    schreibenScore: raw.schreiben_score,
    sprechenScore: raw.sprechen_score,
    pdfUrl: raw.pdf_url,
    qrCodeUrl: raw.qr_code_url,
    isValid: raw.is_valid,
    issuedAt: raw.issued_at,
  };
}

export async function listCertificates(): Promise<AdminCertificateItem[]> {
  const response = await api.get(BASE_PATH);
  return response.data.map(mapCertificate);
}

export async function issueCertificate(
  input: IssueCertificateInput,
): Promise<AdminCertificateItem> {
  const response = await api.post(BASE_PATH, {
    user_id: input.userId,
    course_id: input.courseId,
    level: input.level,
    lesen_score: input.lesenScore,
    hoeren_score: input.hoerenScore,
    schreiben_score: input.schreibenScore,
    sprechen_score: input.sprechenScore,
    provider: input.provider ?? "VIZU",
  });
  return mapCertificate(response.data);
}

export async function updateCertificate(
  certificateId: string,
  input: UpdateCertificateInput,
): Promise<AdminCertificateItem> {
  const response = await api.put(`${BASE_PATH}/${certificateId}`, {
    score: input.score,
    lesen_score: input.lesenScore,
    hoeren_score: input.hoerenScore,
    schreiben_score: input.schreibenScore,
    sprechen_score: input.sprechenScore,
    pdf_url: input.pdfUrl,
    qr_code_url: input.qrCodeUrl,
    is_valid: input.isValid,
  });
  return mapCertificate(response.data);
}

export async function revokeCertificate(certificateId: string): Promise<void> {
  await api.delete(`${BASE_PATH}/${certificateId}`);
}
