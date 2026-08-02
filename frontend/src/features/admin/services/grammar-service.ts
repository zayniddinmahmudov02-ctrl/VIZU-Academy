import { createCrudApi } from "../lib/crud-api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type { Grammar, GrammarCreate, GrammarUpdate } from "../types/content.types";

export const grammarApi = createCrudApi<Grammar, GrammarCreate, GrammarUpdate>(
  ADMIN_ENDPOINTS.grammar,
);
