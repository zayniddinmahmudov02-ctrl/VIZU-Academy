import { createCrudApi } from "../lib/crud-api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type { ModuleCreate, ModuleItem, ModuleUpdate } from "../types/content.types";

export const modulesApi = createCrudApi<ModuleItem, ModuleCreate, ModuleUpdate>(
  ADMIN_ENDPOINTS.modules,
);
