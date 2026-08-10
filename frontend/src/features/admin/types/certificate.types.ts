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

export interface CertificateHolder {
  user_id: string;
  email: string | null;
  username: string | null;
  first_name: string | null;
  last_name: string | null;
  profile_image: string | null;
  certificate_count: number;
  last_certificate_at: string | null;
}

export interface CertificateHolderListResponse {
  items: CertificateHolder[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// "COURSE" is the only real value today — VORBEREITUNG/VIZU_MOCK don't
// issue certificates yet. Kept as a union so the UI already renders any
// future value correctly once the backend `source` column lands.
export type CertificateSource = "COURSE" | "VORBEREITUNG" | "VIZU_MOCK";

export interface UserCertificateEntry {
  id: string;
  certificate_number: string;
  level: string;
  source: CertificateSource;
  score: number;
  is_valid: boolean;
  issued_at: string;
  pdf_url: string | null;
}
