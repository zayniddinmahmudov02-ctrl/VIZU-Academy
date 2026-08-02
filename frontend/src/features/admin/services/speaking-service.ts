import { createCrudApi } from "../lib/crud-api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type { Speaking, SpeakingCreate, SpeakingUpdate } from "../types/content.types";

export const speakingApi = createCrudApi<Speaking, SpeakingCreate, SpeakingUpdate>(
  ADMIN_ENDPOINTS.speakings,
);
