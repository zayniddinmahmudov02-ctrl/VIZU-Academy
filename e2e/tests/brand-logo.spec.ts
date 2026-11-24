import { expect, test, type Page } from "@playwright/test";

import { ADMIN, API_URL, apiToken, createStudent, loginViaForm, PASSWORD, useLanguage } from "./helpers";

/** The official VIZU-DEUTSCH logo (owner's file, 2026-11-24) is the only logo: every place shows the /branding image — square,
 * not stretched, not cut by its container, sharp enough for the screen — never the old hand-drawn mark; favicon,
 * apple-touch-icon and the PWA icons come from /branding too. Desktop project: 5 screen sizes; Pixel 7 project: its own screen. */

const SIZES = [
  { name: "desktop", width: 1440, height: 900 },
  { name: "laptop", width: 1280, height: 800 },
  { name: "tablet", width: 820, height: 1180 },
  { name: "android", width: 412, height: 915 },
  { name: "iphone", width: 390, height: 844 },
];
const TAG = `${Date.now().toString(36)}`;
const TEACHER = { username: `t_logo_${TAG}`, password: "LogoLehrer2026x" };

async function api(method: string, path: string, token: string, body?: unknown) {
  const res = await fetch(`${API_URL}/api/v1${path}`, {
    method, headers: { Authorization: `Bearer ${token}`, ...(body ? { "Content-Type": "application/json" } : {}) }, body: body ? JSON.stringify(body) : undefined,
  });
  return { status: res.status, json: await res.json().catch(() => null) };
}

async function checkLogos(page: Page, where: string) {
  const logos = page.locator('img[data-testid="brand-logo"]');
  await expect.poll(async () => {
    for (const img of await logos.all()) if (await img.isVisible()) return true;
    return false;
  }, { message: `${where}: a visible logo`, timeout: 20_000 }).toBe(true);
  const dpr = await page.evaluate(() => window.devicePixelRatio);
  for (const img of await logos.all()) {
    if (!(await img.isVisible())) continue;
    await img.scrollIntoViewIfNeeded();
    await expect.poll(() => img.evaluate((el: HTMLImageElement) => el.complete && el.naturalWidth > 0), { message: `${where}: logo loaded` }).toBe(true);
    const info = await img.evaluate((el: HTMLImageElement) => {
      const r = el.getBoundingClientRect();
      let clipped = false;
      for (let a = el.parentElement; a; a = a.parentElement) {
        const s = getComputedStyle(a);
        if (s.overflowX !== "visible" || s.overflowY !== "visible") {
          const p = a.getBoundingClientRect();
          if (r.left < p.left - 1 || r.right > p.right + 1 || r.top < p.top - 1 || r.bottom > p.bottom + 1) clipped = true;
        }
      }
      return { src: el.currentSrc, nw: el.naturalWidth, nh: el.naturalHeight, w: r.width, h: r.height, left: r.left, right: r.right, fit: getComputedStyle(el).objectFit, clipped };
    });
    const label = `${where} (${info.src.split("/").pop()} ${Math.round(info.w)}px)`;
    expect(info.src, label).toMatch(/\/branding\/vizu-logo(-\d+)?\.png$/);
    expect(Math.abs(info.nw - info.nh), `${label}: square file`).toBeLessThanOrEqual(1);
    expect(Math.abs(info.w - info.h), `${label}: not stretched`).toBeLessThanOrEqual(1);
    expect(info.fit, label).toBe("contain");
    expect(info.w, `${label}: not too small`).toBeGreaterThanOrEqual(24);
    expect(info.clipped, `${label}: not cut by a container`).toBe(false);
    expect(info.left, `${label}: inside the screen`).toBeGreaterThanOrEqual(-1);
    expect(info.right, `${label}: inside the screen`).toBeLessThanOrEqual(page.viewportSize()!.width + 1);
    // with a w-srcset, naturalWidth is density-corrected: take the real file width from the name (master = 573 px)
    const filePx = Number(/vizu-logo-(\d+)\.png$/.exec(info.src)?.[1] ?? 573);
    expect(filePx, `${label}: sharp (file ≥ rendered device pixels)`).toBeGreaterThanOrEqual(Math.floor(info.w * Math.min(dpr, 2)));
  }
  expect(await page.locator('svg ellipse[cx="50"][cy="24"]').count(), `${where}: old drawn mark`).toBe(0);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow, `${where}: no horizontal scroll`).toBeLessThanOrEqual(1);
}

async function eachSize(page: Page, isMobile: boolean, run: (size: string) => Promise<void>) {
  if (isMobile) return run("pixel7");
  for (const s of SIZES) {
    await page.setViewportSize({ width: s.width, height: s.height });
    await run(s.name);
  }
}

test("public pages: login, register, forgot password, welcome, download, offline", async ({ page, isMobile }) => {
  test.setTimeout(180_000);
  await useLanguage(page, "de");
  await eachSize(page, isMobile, async (size) => {
    for (const path of ["/", "/login", "/register", "/forgot-password", "/download", "/download/android", "/offline"]) {
      await page.goto(path);
      await checkLogos(page, `${path} @${size}`);
    }
  });
});

test("student panel: sidebar / mobile header on dashboard and Medien", async ({ page, isMobile }) => {
  test.setTimeout(180_000);
  const email = await createStudent();
  await useLanguage(page, "de");
  await loginViaForm(page, email, PASSWORD);
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 20_000 });
  await eachSize(page, isMobile, async (size) => {
    for (const path of ["/dashboard", "/medien", "/medien/bibliothek", "/vorbereitung"]) {
      await page.goto(path);
      await page.waitForTimeout(1200);
      await checkLogos(page, `student ${path} @${size}`); // sidebar (≥ 1024 px) or the header
    }
    if (page.viewportSize()!.width < 1024) {
      await expect(page.getByTestId("header-logo")).toBeVisible();
      await page.getByTestId("header-menu").click();
      await expect(page.getByTestId("mobile-logout")).toBeVisible();
      await checkLogos(page, `student menu drawer @${size}`);
    }
  });
});

test("teacher panel and admin panel", async ({ page, browser, isMobile }) => {
  test.setTimeout(240_000);
  const admin = await apiToken(ADMIN.email, ADMIN.password);
  const created = await api("POST", "/admin/team/teachers", admin, { full_name: `Logo Lehrkraft ${TAG}`, username: TEACHER.username, password: "Vorlaeufig2026xy" });
  expect(created.status, JSON.stringify(created.json)).toBe(201);
  const first = await apiToken(TEACHER.username, "Vorlaeufig2026xy");
  expect((await fetch(`${API_URL}/api/v1/users/me/password`, { method: "PUT", headers: { Authorization: `Bearer ${first}`, "Content-Type": "application/json" },
                                                           body: JSON.stringify({ current_password: "Vorlaeufig2026xy", new_password: TEACHER.password }) })).status).toBe(200);
  await useLanguage(page, "de");
  await loginViaForm(page, TEACHER.username, TEACHER.password);
  await expect(page).toHaveURL(/\/teacher$/, { timeout: 20_000 });
  await eachSize(page, isMobile, async (size) => {
    for (const path of ["/teacher", "/teacher/students", "/teacher/kontroll"]) {
      await page.goto(path);
      await page.waitForTimeout(1000);
      await checkLogos(page, `teacher ${path} @${size}`); // sidebar (≥ 1024 px) or the header next to the menu button
    }
    if (page.viewportSize()!.width < 1024) {
      await page.getByTestId("teacher-menu-button").click();
      await checkLogos(page, `teacher menu drawer @${size}`);
    }
  });

  if (isMobile) return; // admin panel: desktop, laptop and tablet sizes in the desktop project
  const adminPage = await (await browser.newContext()).newPage();
  await useLanguage(adminPage, "de");
  await loginViaForm(adminPage, ADMIN.email, ADMIN.password);
  await adminPage.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
  await adminPage.getByRole("button", { name: "Bestätigen" }).click();
  await expect(adminPage).toHaveURL(/\/admin/, { timeout: 20_000 });
  for (const s of SIZES.slice(0, 3)) {
    await adminPage.setViewportSize({ width: s.width, height: s.height });
    for (const path of ["/admin", "/admin/team", "/admin/app-management"]) {
      await adminPage.goto(path);
      await adminPage.waitForTimeout(1000);
      await checkLogos(adminPage, `admin ${path} @${s.name}`); // sidebar (≥ 1024 px) or the header
    }
    if (s.width < 1024) {
      await adminPage.getByTestId("admin-menu-button").click();
      await adminPage.waitForTimeout(500);
      await checkLogos(adminPage, `admin menu drawer @${s.name}`);
    }
  }
  await adminPage.context().close();
});

test("favicon, apple-touch-icon and manifest icons are the official logo; the old files are gone", async ({ page }) => {
  const requested: string[] = [];
  page.on("request", (r) => requested.push(new URL(r.url()).pathname));
  await page.goto("/login");
  const hrefs = await page.locator('link[rel="icon"], link[rel="apple-touch-icon"]').evaluateAll((els) => els.map((e) => e.getAttribute("href") ?? ""));
  expect(hrefs.some((h) => h.startsWith("/favicon.ico"))).toBe(true);
  expect(hrefs.some((h) => h.startsWith("/branding/apple-touch-icon.png"))).toBe(true);
  for (const h of hrefs) {
    expect(h).toMatch(/^\/(favicon\.ico|branding\/)/);
    const res = await page.request.get(h);
    expect(res.status(), h).toBe(200);
    expect(res.headers()["content-type"], h).toMatch(/^image\//);
  }
  const ico = await (await page.request.get("/favicon.ico")).body();
  expect(ico.readUInt16LE(4), "favicon.ico holds 16, 32 and 48 px").toBe(3);
  const manifest = await (await page.request.get("/manifest.webmanifest")).json();
  for (const icon of manifest.icons as { src: string }[]) expect((await page.request.get(icon.src)).status(), icon.src).toBe(200);
  const original = await page.request.get("/branding/vizu-logo-original.jpg");
  expect(original.status()).toBe(200);
  expect((await original.body()).length, "the owner's file, byte for byte").toBe(69247);
  for (const old of ["/icon.svg", "/icons/icon-192.png", "/icons/apple-touch-icon.png"]) expect((await page.request.get(old)).status(), old).toBe(404);
  expect(requested.filter((p) => p.startsWith("/icons/") || p === "/icon.svg")).toEqual([]);
});
