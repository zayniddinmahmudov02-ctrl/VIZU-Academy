export interface AdminCertificateItem {
  id: string;
  userId: string;
  courseId: string;
  certificateNumber: string;
  verificationCode: string;
  provider: string;
  level: string;
  score: number;
  lesenScore: number;
  hoerenScore: number;
  schreibenScore: number;
  sprechenScore: number;
  pdfUrl: string | null;
  qrCodeUrl: string | null;
  isValid: boolean;
  issuedAt: string;
}

export interface IssueCertificateInput {
  userId: string;
  courseId: string;
  level: string;
  lesenScore: number;
  hoerenScore: number;
  schreibenScore: number;
  sprechenScore: number;
  provider?: string;
}

export interface UpdateCertificateInput {
  score?: number;
  lesenScore?: number;
  hoerenScore?: number;
  schreibenScore?: number;
  sprechenScore?: number;
  pdfUrl?: string;
  qrCodeUrl?: string;
  isValid?: boolean;
}
