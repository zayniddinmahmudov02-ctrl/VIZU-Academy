/** Guards every "list" API response at the network boundary so a malformed
 * backend payload (an error envelope, `null`, a paginated `{items: []}`
 * shape hit by the wrong accessor, etc.) becomes an empty list instead of
 * crashing every downstream `.map()`/`.filter()` call with "X.map is not a
 * function". Call this once where `response.data` is received — never
 * downstream, so callers can keep treating the result as a plain array. */
export function ensureArray<T>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data !== null && data !== undefined && process.env.NODE_ENV !== "production") {
    console.warn("Expected an array from the API but got:", data);
  }
  return [];
}
