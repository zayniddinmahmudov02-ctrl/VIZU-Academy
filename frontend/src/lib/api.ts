import { API_URL } from "@/constants/api";
import { getToken } from "@/src/lib/token";

export async function api<T>(
  endpoint: string,
  options?: RequestInit,
): Promise<T> {

  const token = getToken();

  const response = await fetch(
    `${API_URL}${endpoint}`,
    {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options?.headers ?? {}),
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      `API Error: ${response.status}`,
    );
  }

  return response.json();

}