import { createCrudApi } from "../lib/crud-api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type { Certificate, CertificateCreate, CertificateUpdate } from "../types/certificate.types";

export const certificatesApi = createCrudApi<Certificate, CertificateCreate, CertificateUpdate>(
  ADMIN_ENDPOINTS.certificates,
);
