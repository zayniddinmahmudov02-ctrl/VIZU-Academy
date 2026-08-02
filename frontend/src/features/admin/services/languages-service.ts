import { createCrudApi } from "../lib/crud-api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type { Language, LanguageCreate, LanguageUpdate } from "../types/content.types";

export const languagesApi = createCrudApi<Language, LanguageCreate, LanguageUpdate>(
  ADMIN_ENDPOINTS.languages,
);
