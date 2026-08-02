// NEXT_PUBLIC_API_URL must be set at build time in production — this
// fallback only exists so local dev works out of the box without a
// .env.local file. A missing/wrong value here means every browser-side
// API call (including the entire admin panel) silently fails, since it
// would try to reach the visitor's own machine instead of the real
// backend.
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";