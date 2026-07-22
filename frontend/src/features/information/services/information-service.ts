import { api } from "@/services/api";

import type { ProjectInformation } from "../types/information";

export async function getInformation() {
  const response = await api.get<ProjectInformation>("/information");
  return response.data;
}
