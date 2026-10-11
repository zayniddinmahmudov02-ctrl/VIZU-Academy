import { createCrudApi } from "../lib/crud-api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type { Reading, ReadingCreate, ReadingUpdate } from "../types/content.types";

export const readingApi = createCrudApi<Reading, ReadingCreate, ReadingUpdate>(ADMIN_ENDPOINTS.readings);
