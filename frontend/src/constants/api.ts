// NEXT_PUBLIC_API_URL is required — there is no localhost/127.0.0.1
// fallback. NEXT_PUBLIC_* variables are inlined into the client bundle at
// build time, so a missing value here must fail the build loudly instead
// of silently shipping a fallback address that would send every
// browser-side API call to the visitor's own machine instead of the real
// backend. Set NEXT_PUBLIC_API_URL in the environment before running
// `next build` (or `next dev` for local development).
const rawApiUrl = process.env.NEXT_PUBLIC_API_URL;

if (!rawApiUrl) {
  throw new Error(
    "[VIZU] NEXT_PUBLIC_API_URL is not set. Refusing to fall back to a " +
      "local address — set NEXT_PUBLIC_API_URL to the real backend URL " +
      "as a build-time environment variable and rebuild.",
  );
}

export const API_URL = rawApiUrl;