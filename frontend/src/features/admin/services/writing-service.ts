import { createCrudApi } from "../lib/crud-api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type { Writing, WritingCreate, WritingUpdate } from "../types/content.types";

export const writingApi = createCrudApi<Writing, WritingCreate, WritingUpdate>(
  ADMIN_ENDPOINTS.writings,
);
