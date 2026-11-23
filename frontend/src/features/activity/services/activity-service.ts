import { API_URL } from "@/constants/api";
import { getToken } from "@/lib/token";
import { api } from "@/services/api";

import type { ActivityContext } from "../lib/activity-context";

export interface HeartbeatBody {
  tab_id: string;
  active: boolean;
  final?: boolean;
  contexts: ActivityContext[];
}

export async function sendHeartbeat(body: HeartbeatBody): Promise<void> {
  await api.post("/api/v1/activity/heartbeat", body);
}

/** The last heartbeat when the page is closed: fetch with keepalive survives the unload (sendBeacon cannot send the token). */
export function sendFinalHeartbeat(body: HeartbeatBody): void {
  const token = getToken();
  if (!token) return;
  try {
    void fetch(`${API_URL}/api/v1/activity/heartbeat`, {
      method: "POST",
      keepalive: true,
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ ...body, final: true }),
    }).catch(() => undefined);
  } catch {
    // the page is going away; nothing to do
  }
}
