// VIZU Academy service worker.
//
// Caching policy (see registration in
// src/components/pwa/service-worker-registration.tsx and the security
// notes below):
//
//   NEVER CACHED, network-only, no fallback at all — auth, payments,
//   admin data. A request matching NEVER_CACHE_PATTERNS is passed
//   straight through to the network and its response is never written
//   to any Cache Storage, regardless of method or status.
//
//   NETWORK-FIRST, cached fallback — every other /api/v1/* GET (lesson
//   content, progress, exams, results, user data). Tries the network
//   first; only on a network failure (offline) does it fall back to the
//   last successful cached copy, if any. A fresh response always
//   overwrites the cached one, so a stale cache is never preferred over
//   live data while online. Never caches non-GET requests (mutations
//   are never replayed from cache).
//
//   CACHE-FIRST — same-origin static build assets (_next/static/*),
//   local icons/fonts, and the manifest. These are content-hashed or
//   effectively immutable, so serving from cache first is safe and
//   fast; falls back to network if not yet cached.
//
//   Navigation (HTML page) requests: network-first; on failure, serves
//   the cached /offline page instead of a raw browser error.
//
// Nothing here ever inspects, stores, or forwards a JWT/auth token —
// tokens live in localStorage/sessionStorage, which a service worker
// has no access to at all; this file only ever deals with HTTP
// response bodies for the URLs listed above.

const STATIC_CACHE = "vizu-static-v1";
const RUNTIME_CACHE = "vizu-runtime-v1";
const OFFLINE_URL = "/offline";

const NEVER_CACHE_PATTERNS = [
  "/api/v1/auth",
  "/api/v1/admin",
  "/api/v1/vizu-pay",
  "/api/v1/payments",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => cache.addAll([OFFLINE_URL])).catch(() => {}),
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key !== STATIC_CACHE && key !== RUNTIME_CACHE)
            .map((key) => caches.delete(key)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

// A logged-out user's page (see src/lib/token.ts) posts this so the
// runtime cache never keeps serving another account's lesson/progress
// data after logout — the static asset cache is untouched (nothing
// sensitive lives there).
self.addEventListener("message", (event) => {
  if (event.data?.type === "CLEAR_RUNTIME_CACHE") {
    event.waitUntil(caches.delete(RUNTIME_CACHE));
  }
});

function isNeverCached(pathname) {
  return NEVER_CACHE_PATTERNS.some((prefix) => pathname.startsWith(prefix));
}

function isStaticAsset(url) {
  return (
    url.origin === self.location.origin &&
    (url.pathname.startsWith("/_next/static/") ||
      url.pathname.startsWith("/icons/") ||
      url.pathname.startsWith("/fonts/") ||
      url.pathname === "/manifest.webmanifest" ||
      url.pathname === "/favicon.ico" ||
      url.pathname === "/icon.svg")
  );
}

function isApiRequest(url) {
  return url.pathname.startsWith("/api/v1/") || url.pathname.startsWith("/api/");
}

async function networkFirst(request, cacheName) {
  try {
    const response = await fetch(request);
    if (response && response.ok && request.method === "GET") {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    const cached = await caches.match(request);
    if (cached) return cached;
    throw err;
  }
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  if (response && response.ok) {
    const cache = await caches.open(STATIC_CACHE);
    cache.put(request, response.clone());
  }
  return response;
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET" && request.method !== "HEAD") {
    // Never intercept/cache mutations (POST/PUT/PATCH/DELETE) at all —
    // straight to network, untouched.
    return;
  }

  const url = new URL(request.url);

  // Never-cache list: bypass this service worker entirely (no cache
  // read, no cache write, no offline fallback) — a failure here should
  // surface as a normal network error, not silently serve stale
  // auth/payment/admin data.
  if (isApiRequest(url) && isNeverCached(url.pathname)) {
    return;
  }

  if (isStaticAsset(url)) {
    event.respondWith(cacheFirst(request));
    return;
  }

  if (isApiRequest(url)) {
    event.respondWith(networkFirst(request, RUNTIME_CACHE));
    return;
  }

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(() => caches.match(OFFLINE_URL).then((res) => res || Response.error())),
    );
  }
  // Everything else (e.g. cross-origin third-party requests) is left
  // completely alone — no respondWith(), default browser handling.
});
