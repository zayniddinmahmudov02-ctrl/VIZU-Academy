import { createCrudApi } from "../lib/crud-api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type { Level, LevelCreate, LevelUpdate } from "../types/content.types";

export const levelsApi = createCrudApi<Level, LevelCreate, LevelUpdate>(
  ADMIN_ENDPOINTS.levels,
);
