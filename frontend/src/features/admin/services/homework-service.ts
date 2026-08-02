import { createCrudApi } from "../lib/crud-api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type { Homework, HomeworkCreate, HomeworkUpdate } from "../types/content.types";

export const homeworkApi = createCrudApi<Homework, HomeworkCreate, HomeworkUpdate>(
  ADMIN_ENDPOINTS.homeworks,
);
