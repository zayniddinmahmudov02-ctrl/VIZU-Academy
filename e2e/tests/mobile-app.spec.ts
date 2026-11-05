import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";

import { expect, test, type Page } from "@playwright/test";

import { ADMIN, API_URL, loginViaForm, useLanguage } from "./helpers";

// VIZU DEUTSCH APP: public /download page (Android APK card, iPhone install guide, desktop QR), Super Admin
// App Management (upload → refuse debug build → publish → download + checksum), and the in-app update prompt
// (window.Capacitor simulated). Local stack only. APKs are built by D:\vz_tmp\work\build_test_apks.ps1 with a
// throwaway TEST key; the debug APK comes from `npm run apk:debug` in mobile/.
const APK_DIR = process.env.E2E_APK_DIR ?? "D:/vz_tmp/work/apk-test";
const APK_V1 = `${APK_DIR}/vizu-1.0.0-test.apk`;
const APK_V2 = `${APK_DIR}/vizu-1.0.1-test.apk`;
const APK_DEBUG = process.env.E2E_APK_DEBUG ?? "D:/Projects/VIZU-Academy/mobile/android/app/build/outputs/apk/debug/app-debug.apk";
const IPHONE_CHROME = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/130.0 Mobile/15E148 Safari/604.1";
const PSQL = process.env.E2E_PSQL ?? "C:/Program Files/PostgreSQL/18/bin/psql.exe";
const DB = process.env.E2E_DB ?? "vizu_gcr_e2e";
const sql = (q: string) => execFileSync(PSQL, ["-h", "127.0.0.1", "-p", "54329", "-U", "postgres", "-d", DB, "-tAc", q], { encoding: "utf8" }).trim();
const IPHONE_SAFARI ="Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1";

async function noHorizontalScroll(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(1);
}

async function adminLogin(page: Page) {
  await useLanguage(page, "de");
  await loginViaForm(page, ADMIN.email, ADMIN.password);
  await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
  await page.getByRole("button", { name: "Bestätigen" }).click();
  await expect(page).toHaveURL(/\/admin/);
}

test.describe.configure({ mode: "serial" });

test("download page: Android card (coming soon until a release exists), iPhone guide, QR on desktop, manifest", async ({ page, isMobile }) => {
  const hasRelease = (await page.request.get(`${API_URL}/api/v1/app/releases/latest`)).status() === 200;
  await useLanguage(page, "de");
  await page.goto("/download");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("VIZU DEUTSCH APP");
  await expect(page.getByTestId("download-slogan")).toHaveText("Lerne Deutsch. Überall. Jederzeit.");
  const android = page.getByTestId("download-android");
  await expect(android).toContainText("VIZU DEUTSCH für Android");
  await expect(android).toContainText("Installiere unsere Android-App direkt auf deinem Smartphone.");
  if (hasRelease) {
    await expect(page.getByTestId("download-apk")).toBeVisible();
  } else {
    await expect(page.getByTestId("download-android-soon")).toBeVisible();
    await expect(page.getByTestId("download-apk")).toHaveCount(0);
    expect((await page.request.get(`${API_URL}/api/v1/app/android/latest.apk`)).status()).toBe(404);
  }
  const ios = page.getByTestId("download-ios");
  await expect(ios).toContainText("VIZU DEUTSCH für iPhone");
  await expect(ios).toContainText("Füge VIZU-DEUTSCH direkt zu deinem Home-Bildschirm hinzu.");
  await page.getByTestId("ios-install").click();
  const guide = page.getByTestId("ios-guide");
  await expect(guide).toBeVisible();
  await expect(guide).toContainText("Öffne vizu-deutsch.com in Safari.");
  await expect(guide).toContainText("„Zum Home-Bildschirm“");
  await page.keyboard.press("Escape");
  await expect(guide).toBeHidden();
  if (isMobile) {
    await expect(page.getByTestId("download-qr")).toHaveCount(0); // Pixel 7 = Android: no QR, Android card first
    const [a, i] = await Promise.all([android.boundingBox(), ios.boundingBox()]);
    expect(a!.y).toBeLessThan(i!.y);
  } else {
    const qr = page.getByTestId("download-qr");
    await expect(qr).toBeVisible();
    const res = await page.request.get(`${API_URL}/api/v1/app/download-qr.svg`);
    expect(res.status()).toBe(200);
    expect(res.headers()["content-type"]).toContain("image/svg+xml");
  }
  await noHorizontalScroll(page);
  const manifest = await (await page.request.get("/manifest.webmanifest")).json();
  expect(manifest).toMatchObject({ name: "VIZU DEUTSCH", short_name: "VIZU", start_url: "/", scope: "/", display: "standalone" });
  expect(manifest.icons.map((i: { sizes: string; purpose: string }) => `${i.sizes}/${i.purpose}`)).toEqual(["192x192/any", "512x512/any", "512x512/maskable"]);
  const apple = await page.locator('link[rel="apple-touch-icon"]').getAttribute("href");
  expect(apple).toBe("/icons/apple-touch-icon.png");
  await expect(page.locator('meta[name="apple-mobile-web-app-capable"]')).toHaveAttribute("content", "yes");
  await expect(page.locator('meta[name="apple-mobile-web-app-title"]')).toHaveAttribute("content", "VIZU DEUTSCH");
  expect(await page.locator('meta[name="viewport"]').getAttribute("content")).toContain("viewport-fit=cover");
});

test.describe("iPhone outside Safari", () => {
  test.use({ userAgent: IPHONE_CHROME, viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
  test("the guide says to open Safari, iPhone card comes first", async ({ page }) => {
    await useLanguage(page, "de");
    await page.goto("/download");
    const [a, i] = await Promise.all([page.getByTestId("download-android").boundingBox(), page.getByTestId("download-ios").boundingBox()]);
    expect(i!.y).toBeLessThan(a!.y);
    await page.getByTestId("ios-install").click();
    await expect(page.getByTestId("ios-guide-not-safari")).toContainText("nicht Safari");
    await noHorizontalScroll(page);
  });
});

test.describe("iPhone Safari", () => {
  test.use({ userAgent: IPHONE_SAFARI, viewport: { width: 360, height: 800 }, hasTouch: true, isMobile: true });
  test("no Safari warning, page fits 360 px", async ({ page }) => {
    await useLanguage(page, "uz");
    await page.goto("/download");
    await expect(page.getByTestId("download-slogan")).toHaveText("Nemis tilini o‘rganing. Istalgan joyda. Istalgan vaqtda.");
    await page.getByTestId("ios-install").click();
    await expect(page.getByTestId("ios-guide")).toBeVisible();
    await expect(page.getByTestId("ios-guide-not-safari")).toHaveCount(0);
    await noHorizontalScroll(page);
  });
});

test("App Management: refuses a debug build, publishes signed releases, version must grow, APK downloads intact", async ({ page, isMobile }) => {
  test.skip(isMobile, "admin checks run on desktop");
  test.skip(!existsSync(APK_V1) || !existsSync(APK_V2), "build the test APKs first (build_test_apks.ps1)");
  sql("DELETE FROM app_releases"); // local E2E database only: a repeatable start
  await adminLogin(page);
  await page.goto("/admin/app-management");
  await expect(page.getByRole("heading", { name: "App Management" })).toBeVisible();
  await expect(page.locator("aside nav, nav").first().getByRole("link", { name: "App Management", exact: true })).toBeVisible();

  if (existsSync(APK_DEBUG)) {
    await page.getByTestId("apk-file").setInputFiles(APK_DEBUG);
    await page.getByTestId("apk-upload").click();
    await expect(page.getByRole("status")).toContainText("Debug-Build erkannt");
  }

  // v1.0.1 (versionCode 2) first, then the older 1.0.0 must not become "latest"
  await page.getByTestId("apk-file").setInputFiles(APK_V2);
  await page.locator("#apk-notes").fill("Neue Battle-Arena und schnellere Lektionen.");
  await page.getByTestId("apk-upload").click();
  await expect(page.getByRole("status")).toContainText("Version 1.0.1 (versionCode 2) als Entwurf hochgeladen");
  const row = page.getByTestId("app-release-row").filter({ hasText: "1.0.1" });
  await expect(row).toHaveAttribute("data-status", "draft");
  await row.getByTestId("app-release-publish").click();
  await expect(row).toHaveAttribute("data-status", "published");
  await expect(row).toContainText("Aktuell");

  await page.getByTestId("apk-file").setInputFiles(APK_V1);
  await page.getByTestId("apk-upload").click();
  await expect(page.getByRole("status")).toContainText("Version 1.0.0 (versionCode 1)");
  await page.getByTestId("app-release-row").filter({ hasText: "1.0.0" }).getByTestId("app-release-publish").click();
  await expect(page.getByRole("status")).toContainText("versionCode muss höher sein");

  // public page now offers 1.0.1 with real metadata, and the file downloads byte-identical
  await page.goto("/download");
  const facts = page.getByTestId("download-android-facts");
  await expect(facts).toContainText("1.0.1");
  await expect(facts).toContainText("Android 7.0 oder neuer");
  await expect(page.getByTestId("download-android")).toContainText("Neue Battle-Arena");
  const expected = createHash("sha256").update(readFileSync(APK_V2)).digest("hex");
  await expect(facts).toContainText(expected.slice(0, 8));
  const href = await page.getByTestId("download-apk").getAttribute("href");
  const res = await page.request.get(href!);
  expect(res.status()).toBe(200);
  expect(res.headers()["content-type"]).toBe("application/vnd.android.package-archive");
  expect(res.headers()["content-disposition"]).toContain("VIZU-DEUTSCH-1.0.1.apk");
  expect(createHash("sha256").update(await res.body()).digest("hex")).toBe(expected);
  // the short link on the site redirects to the same file
  const short = await page.request.get("/downloads/android/latest.apk", { maxRedirects: 0 });
  expect([307, 308]).toContain(short.status());
  expect(short.headers()["location"]).toContain("/api/v1/app/android/latest.apk");
});

test("installed Android app 1.0.0 is offered the 1.0.1 update; browsers are not", async ({ page, isMobile }) => {
  test.skip(!isMobile, "runs once, on the phone project");
  const latest = await page.request.get(`${API_URL}/api/v1/app/releases/latest`);
  test.skip(latest.status() !== 200, "needs the published release from the previous test");
  await useLanguage(page, "de");
  await page.goto("/");
  await expect(page.getByTestId("app-update-prompt")).toHaveCount(0);
  await expect(page.getByTestId("app-download-link")).toBeVisible();

  await page.addInitScript(() => {
    (window as unknown as { Capacitor: unknown }).Capacitor = {
      isNativePlatform: () => true,
      getPlatform: () => "android",
      Plugins: { App: { getInfo: async () => ({ name: "VIZU DEUTSCH", id: "com.vizu.deutsch", build: "1", version: "1.0.0" }) } },
    };
  });
  await page.goto("/");
  const prompt = page.getByTestId("app-update-prompt");
  await expect(prompt).toBeVisible({ timeout: 15_000 });
  await expect(prompt).toContainText("Version 1.0.1 ist da (installiert: 1.0.0)");
  await expect(prompt).toContainText("Neue Battle-Arena");
  await expect(prompt.getByRole("link", { name: /Update herunterladen/ })).toHaveAttribute("href", /\/api\/v1\/app\/android\/latest\.apk$/);
  await expect(page.getByTestId("app-download-link")).toHaveCount(0); // already the app: no "download the app" link
  await prompt.getByRole("button", { name: "Später" }).click();
  await expect(prompt).toBeHidden();
  await page.reload();
  await expect(page.getByTestId("app-update-prompt")).toHaveCount(0); // "later" holds for this session
});
