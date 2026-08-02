import { createCrudApi } from "../lib/crud-api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type { Listening, ListeningCreate, ListeningUpdate } from "../types/content.types";

export const listeningApi = createCrudApi<Listening, ListeningCreate, ListeningUpdate>(
  ADMIN_ENDPOINTS.listenings,
);
