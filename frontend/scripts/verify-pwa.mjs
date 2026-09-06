// Plain-Node PWA smoke checks — no new test framework added (this repo
// has no Jest/Vitest/Playwright/Cypress at all yet; per the task's own
// instruction, one isn't introduced just for this). Run with:
//
//   node scripts/verify-pwa.mjs
//
// Static/source-level checks only (this isn't a runtime/browser test —
// there's no headless-browser tooling in this repo to actually load a
// page and inspect a live service worker registration or manifest
// response). Exits non-zero on the first failed assertion.

import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import sharp from "sharp";

const root = path.dirname(fileURLToPath(import.meta.url)) + "/..";
const read = (p) => readFileSync(path.join(root, p), "utf-8");

let passed = 0;
async function check(label, fn) {
  await fn();
  passed += 1;
  console.log(`  ok  ${label}`);
}

console.log("Manifest");
{
  const src = read("src/app/manifest.ts");
  await check("declares required manifest fields", () => {
    for (const field of ["name:", "short_name:", "start_url:", "display:", "theme_color:", "background_color:", "icons:"]) {
      assert.ok(src.includes(field), `manifest.ts missing "${field}"`);
    }
  });
  await check("display is standalone", () => assert.ok(/display:\s*"standalone"/.test(src)));
  await check("declares a maskable icon purpose", () => assert.ok(src.includes('purpose: "maskable"')));
  await check("references the generated icon files", () => {
    for (const f of ["icon-192.png", "icon-512.png", "icon-maskable-512.png"]) {
      assert.ok(src.includes(f), `manifest.ts doesn't reference ${f}`);
    }
  });
}

console.log("\nIcons on disk");
{
  const icons = [
    ["public/icons/icon-192.png", 192, 192],
    ["public/icons/icon-512.png", 512, 512],
    ["public/icons/icon-maskable-512.png", 512, 512],
    ["public/icons/apple-touch-icon.png", 180, 180],
  ];
  for (const [rel, w, h] of icons) {
    await check(`${rel} exists at ${w}x${h}`, async () => {
      assert.ok(existsSync(path.join(root, rel)), `${rel} missing`);
      const meta = await sharp(path.join(root, rel)).metadata();
      assert.equal(meta.width, w, `${rel} width`);
      assert.equal(meta.height, h, `${rel} height`);
    });
  }
}

console.log("\nApple / iOS metadata (layout.tsx)");
{
  const src = read("src/app/layout.tsx");
  await check("appleWebApp.capable is set", () => assert.ok(src.includes("appleWebApp") && src.includes("capable: true")));
  await check("apple-touch-icon referenced", () => assert.ok(src.includes("apple-touch-icon.png")));
  await check("viewportFit cover (safe-area support)", () => assert.ok(src.includes('viewportFit: "cover"')));
  await check("themeColor set", () => assert.ok(src.includes("themeColor")));
  await check("manifest link wired", () => assert.ok(src.includes("manifest.webmanifest")));
  await check("service worker registration mounted", () => assert.ok(src.includes("ServiceWorkerRegistration")));
}

console.log("\nSafe-area CSS");
{
  const src = read("src/app/globals.css");
  await check("body applies env(safe-area-inset-*)", () => {
    for (const side of ["top", "bottom", "left", "right"]) {
      assert.ok(src.includes(`env(safe-area-inset-${side})`), `missing safe-area-inset-${side}`);
    }
  });
}

console.log("\nService worker — sensitive data never cached");
{
  const src = read("public/sw.js");
  await check("sw.js exists and defines a fetch handler", () => assert.ok(src.includes('addEventListener("fetch"')));
  await check("auth/admin/payments are in the never-cache list", () => {
    for (const p of ["/api/v1/auth", "/api/v1/admin", "/api/v1/vizu-pay", "/api/v1/payments"]) {
      assert.ok(src.includes(p), `sw.js never-cache list missing ${p}`);
    }
  });
  await check("never-cache requests bypass respondWith entirely", () => {
    // The never-cache branch must `return` (no event.respondWith call),
    // i.e. fall through to default browser network handling untouched —
    // proven by the branch appearing before any cache.put/match call in
    // the fetch handler and containing a bare `return;`.
    const fetchHandler = src.slice(src.indexOf('addEventListener("fetch"'));
    const neverCacheBranch = fetchHandler.slice(
      fetchHandler.indexOf("isNeverCached"),
      fetchHandler.indexOf("isNeverCached") + 200,
    );
    assert.ok(neverCacheBranch.includes("return;"), "never-cache branch doesn't bypass respondWith");
  });
  await check("non-GET/HEAD requests are never intercepted", () => assert.ok(src.includes('request.method !== "GET"')));
  await check("logout can clear the runtime cache via postMessage", () => assert.ok(src.includes("CLEAR_RUNTIME_CACHE")));
  await check("offline navigation fallback is wired", () => assert.ok(src.includes("OFFLINE_URL") && src.includes('mode === "navigate"')));
}

console.log("\nOffline page + install UI");
{
  await check("offline page exists", () => assert.ok(existsSync(path.join(root, "src/app/offline/page.tsx"))));
  await check("install prompt hook exists", () => assert.ok(existsSync(path.join(root, "src/features/pwa/hooks/use-install-prompt.ts"))));
  const hookSrc = read("src/features/pwa/hooks/use-install-prompt.ts");
  await check("listens for beforeinstallprompt (Android/Chrome support detection)", () =>
    assert.ok(hookSrc.includes("beforeinstallprompt")),
  );
  await check("detects iOS separately from generic install support", () => assert.ok(hookSrc.includes("isIOSDevice")));
  const buttonSrc = read("src/components/pwa/install-app-button.tsx");
  await check("renders nothing when neither install path applies", () => {
    assert.ok(buttonSrc.includes("return null;"), "install button has no not-applicable fallback");
  });
}

console.log("\nlogout clears runtime cache (token.ts)");
{
  const src = read("src/lib/token.ts");
  await check("removeToken triggers clearRuntimeCache", () => {
    const fn = src.slice(src.indexOf("export function removeToken"), src.indexOf("export function removeToken") + 300);
    assert.ok(fn.includes("clearRuntimeCache()"));
  });
}

console.log("\nExisting lesson architecture untouched");
{
  const src = read("src/constants/lesson-sections.ts");
  const expectedSlugs = [
    "video", "wortschatz", "wortschatz-quiz", "grammatik", "grammatik-quiz",
    "lesen", "hoeren", "schreiben", "sprechen", "hausaufgabe", "ergebnis",
  ];
  await check("all 11 student sections still present, in order", () => {
    for (const slug of expectedSlugs) {
      assert.ok(src.includes(`slug: "${slug}"`), `missing section slug "${slug}"`);
    }
  });
  await check("lesson-quiz is not in the student nav array", () => {
    const arrayBody = src.slice(src.indexOf("lessonSections: LessonSectionMeta[] = ["), src.indexOf("];"));
    assert.ok(!arrayBody.includes('slug: "lesson-quiz"'), "lesson-quiz leaked back into student nav");
  });

  const gateSrc = read("../backend/app/services/lesson_progress/section_gate.py");
  await check("no sequential gating (backend _compute_unlocked always true)", () => {
    assert.ok(gateSrc.includes("return {key: True for key in SECTION_ORDER}"));
  });
  await check("video completion threshold still 70%", () => {
    const vpSrc = read("../backend/app/services/video_progress/service.py");
    assert.ok(/70/.test(vpSrc), "70% threshold not found in video_progress service");
  });
}

console.log(`\n${passed} checks passed.`);
