import { createCrudApi } from "../lib/crud-api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type { Vocabulary, VocabularyCreate, VocabularyUpdate } from "../types/content.types";

export const vocabularyApi = createCrudApi<Vocabulary, VocabularyCreate, VocabularyUpdate>(
  ADMIN_ENDPOINTS.vocabularies,
);
