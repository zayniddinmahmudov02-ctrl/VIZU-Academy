import { api } from "@/services/api";

import type { ActivityTypeConfig } from "../config/lesson-activity-configs";

export type ActivityRecord = Record<string, unknown> & { id: string; lesson_id: string };

function listPath(config: ActivityTypeConfig): string {
  return config.trailingSlash ? `${config.apiBase}/` : config.apiBase;
}

export async function listActivityItems(config: ActivityTypeConfig): Promise<ActivityRecord[]> {
  const response = await api.get(listPath(config));
  return response.data;
}

export async function createActivityItem(
  config: ActivityTypeConfig,
  payload: Record<string, unknown>,
): Promise<ActivityRecord> {
  const response = await api.post(listPath(config), payload);
  return response.data;
}

export async function updateActivityItem(
  config: ActivityTypeConfig,
  itemId: string,
  payload: Record<string, unknown>,
): Promise<ActivityRecord> {
  const response = await api.put(`${config.apiBase}/${itemId}`, payload);
  return response.data;
}

export async function deleteActivityItem(config: ActivityTypeConfig, itemId: string): Promise<void> {
  await api.delete(`${config.apiBase}/${itemId}`);
}
