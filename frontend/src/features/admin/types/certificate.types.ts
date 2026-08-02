export interface Certificate {
  id: string;
  user_id: string;
  course_id: string;
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
  certificate_number: string;
  verification_code: string;
  issued_at: string;
}

export interface CertificateCreate {
  user_id: string;
  course_id: string;
  provider?: string;
  level: string;
  score?: number;
  lesen_score?: number;
  hoeren_score?: number;
  schreiben_score?: number;
  sprechen_score?: number;
  is_valid?: boolean;
}

export type CertificateUpdate = Partial<CertificateCreate>;
