// NEXT_PUBLIC_API_URL must be set at build time in production — this
// fallback only exists so local dev works out of the box without a
// .env.local file. A missing/wrong value here means every browser-side
// API call (including the entire admin panel) silently fails, since it
// would try to reach the visitor's own machine instead of the real
// backend.
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

if (process.env.NODE_ENV === "production" && !process.env.NEXT_PUBLIC_API_URL) {
  // This runs in the browser too (NODE_ENV is inlined at build time), so
  // a misconfigured deploy shows up loudly in the browser console instead
  // of silently sending every request to the visitor's own machine.
  console.error(
    "[VIZU] NEXT_PUBLIC_API_URL is not set in this production build — " +
      `falling back to ${API_URL}, which is almost certainly wrong. ` +
      "Set NEXT_PUBLIC_API_URL to the real backend URL and rebuild.",
  );
}