import { execFileSync } from "node:child_process";
import { deflateSync } from "node:zlib";

import { expect, test, type Page } from "@playwright/test";

import { createStudent, loginViaForm, PASSWORD, useLanguage } from "./helpers";

// Battle on the dashboard, open access, custom icon, profile photo (upload / crop / replace / remove) and the
// photo on Battle screens. Local stack only; `psql` is used to give one test user a premium period.

const PSQL = process.env.E2E_PSQL ?? "C:/Program Files/PostgreSQL/18/bin/psql.exe";
const DB = process.env.E2E_DB ?? "vizu_gcr_e2e";

function sql(q: string) {
  return execFileSync(PSQL, ["-h", "127.0.0.1", "-p", "54329", "-U", "postgres", "-d", DB, "-tAc", q], { encoding: "utf8" }).trim();
}

const CRC = Array.from({ length: 256 }, (_, n) => {
  let c = n;
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  return c >>> 0;
});
function crc32(buf: Buffer) {
  let c = 0xffffffff;
  for (const b of buf) c = CRC[(c ^ b) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}
/** A real RGB PNG (two colour halves) without any image library. */
function png(w: number, h: number): Buffer {
  const chunk = (type: string, data: Buffer) => {
    const len = Buffer.alloc(4);
    len.writeUInt32BE(data.length);
    const td = Buffer.concat([Buffer.from(type), data]);
    const crc = Buffer.alloc(4);
    crc.writeUInt32BE(crc32(td));
    return Buffer.concat([len, td, crc]);
  };
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(w, 0);
  ihdr.writeUInt32BE(h, 4);
  ihdr.set([8, 2, 0, 0, 0], 8);
  const rows = [];
  for (let y = 0; y < h; y++) {
    const row = Buffer.alloc(1 + w * 3);
    for (let x = 0; x < w; x++) row.set(x < w / 2 ? [57, 132, 232] : [242, 196, 91], 1 + x * 3);
    rows.push(row);
  }
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk("IHDR", ihdr), chunk("IDAT", deflateSync(Buffer.concat(rows))), chunk("IEND", Buffer.alloc(0))]);
}

async function login(page: Page) {
  const email = await createStudent();
  await useLanguage(page, "de");
  await loginViaForm(page, email, PASSWORD);
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 20_000 });
  return email;
}

test("anonymous visitors are sent to the login page", async ({ page }) => {
  await page.goto("/battle");
  await expect(page).toHaveURL(/\/login/, { timeout: 15_000 });
});

test("dashboard: Battle banner on top for a new student without any course, icon in the navigation", async ({ page, isMobile }) => {
  await login(page);
  const banner = page.getByTestId("dashboard-battle-banner");
  const tools = page.getByTestId("dashboard-learning-tools");
  await expect(banner).toBeVisible();
  await expect(banner).toContainText("VIZU DEUTSCH BATTLE");
  await expect(banner).toContainText("Fordere andere Spieler heraus und verbessere dein Deutsch!");
  await expect(page.getByTestId("battle-banner-first")).toHaveText("Starte deine erste Battle!");
  await expect(page.getByTestId("battle-banner-rank")).toHaveText("A1-Einsteiger");
  await expect(banner.locator('svg[data-icon="battle"]')).toHaveCount(1);
  await expect(tools.getByRole("heading", { name: "Lernwerkzeuge" })).toBeVisible();
  await expect(tools.getByRole("link", { name: "Stufe Bestimmung öffnen" })).toBeVisible();
  await expect(tools.getByRole("link", { name: "Wortschatz öffnen" })).toHaveAttribute("href", "/woerterbuch");
  await expect(tools.getByRole("link", { name: "Zertifikatsprüfungen öffnen" })).toHaveAttribute("href", "/vorbereitung");
  await expect(page.getByRole("heading", { name: "A1–C1 Kurse" })).toBeVisible();
  await expect(page.getByTestId("dashboard-course")).toHaveCount(5);
  await expect(page.getByTestId("dashboard-stats")).toBeVisible();
  await expect(page.getByTestId("dashboard-achievements")).toHaveCount(0);
  await expect(page.getByTestId("dashboard-certificates")).toHaveCount(0);

  await tools.getByRole("link", { name: "Stufe Bestimmung öffnen" }).click();
  await expect(page).toHaveURL(/\/vizu-multilevel$/);
  await expect(page.getByRole("heading", { name: "Stufe Bestimmung" })).toBeVisible();
  await expect(page.getByText("Bestimme dein aktuelles Deutschniveau.")).toBeVisible();
  await page.goto("/dashboard");
  await page.getByTestId("dashboard-learning-tools").getByRole("link", { name: "Wortschatz öffnen" }).click();
  await expect(page).toHaveURL(/\/woerterbuch$/);
  await page.goto("/dashboard");

  const bannerBox = await banner.boundingBox();
  const courseBox = await page.getByTestId("dashboard-course").first().boundingBox();
  expect(bannerBox!.y).toBeLessThan(courseBox!.y);
  // visible without scrolling (the compact Werbung banner sits above it since 2026-11-05)
  if (!isMobile) expect(bannerBox!.y + 60).toBeLessThan(page.viewportSize()!.height);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(1);
  if (!isMobile) await expect(page.locator('aside a[href="/battle"] svg[data-icon="battle"]')).toHaveCount(1);

  await page.getByTestId("battle-banner-cta").click();
  await expect(page).toHaveURL(/\/battle$/);
  await expect(page.getByTestId("battle-home")).toBeVisible({ timeout: 15_000 });
  await expect(page.getByTestId("battle-nav").locator('svg[data-icon="battle"]').first()).toBeVisible();
  await expect(page.locator('link[rel="icon"][href*="battle-icon.svg"]')).toHaveCount(1);
});

test("a student with a premium period plays exactly like everybody else", async ({ page }) => {
  const email = await login(page);
  sql(`UPDATE users SET premium_until = now() + interval '30 days' WHERE email = '${email}'`);
  await page.goto("/battle");
  await expect(page.getByTestId("battle-start")).toBeEnabled({ timeout: 15_000 });
  await page.getByTestId("battle-practice").click();
  await expect(page.getByTestId("battle-countdown").or(page.getByTestId("battle-arena"))).toBeVisible({ timeout: 15_000 });
});

test("profile photo: crop + upload, shown in Battle and leaderboard, wrong file rejected, replace, remove", async ({ page }) => {
  test.setTimeout(90_000);
  await login(page);
  await page.goto("/settings");
  await page.getByTestId("profile-photo-input").setInputFiles({ name: "ich.png", mimeType: "image/png", buffer: png(400, 300) });
  await expect(page.getByTestId("photo-cropper")).toBeVisible();
  await page.getByTestId("photo-crop-zoom").fill("2");
  const uploaded = page.waitForResponse((r) => r.url().includes("/users/me/photo") && r.request().method() === "POST");
  await page.getByTestId("profile-photo-save").click();
  const res = await uploaded;
  expect(res.status()).toBe(200);
  expect((await res.json()).profile_image).toMatch(/^\/uploads\/avatars\/[0-9a-f]{32}\.webp$/);
  const card = page.getByTestId("profile-photo-card");
  await expect(card.getByTestId("profile-photo-remove")).toBeVisible({ timeout: 15_000 });

  // a text file that claims to be a PNG passes the browser check but not the server's
  await page.getByTestId("profile-photo-input").setInputFiles({ name: "fake.png", mimeType: "image/png", buffer: Buffer.from("<svg onload=alert(1)>not an image") });
  await page.getByTestId("profile-photo-save").click();
  await expect(page.getByTestId("profile-photo-error")).toContainText("kein gültiges Bild");
  await page.getByRole("button", { name: "Abbrechen" }).click();

  await page.goto("/battle");
  await expect(page.getByTestId("battle-home").getByTestId("player-photo").first()).toBeVisible({ timeout: 15_000 });
  await expect(page.getByTestId("battle-nav").getByTestId("player-photo")).toBeVisible();
  await page.goto("/battle/rangliste");
  await expect(page.getByTestId("battle-leaderboard").getByTestId("player-photo").first()).toBeVisible({ timeout: 15_000 });

  // replace from inside Battle, then remove → the 3D avatar comes back
  await page.goto("/battle?avatar=1");
  await page.getByTestId("battle-photo-input").setInputFiles({ name: "neu.png", mimeType: "image/png", buffer: png(300, 300) });
  await page.getByTestId("battle-photo-save").click();
  await expect(page.getByTestId("battle-photo-remove")).toBeVisible({ timeout: 15_000 });
  await page.getByTestId("battle-photo-remove").click();
  await expect(page.getByTestId("battle-photo-pick")).toHaveText(/Hochladen/, { timeout: 15_000 });
  await page.keyboard.press("Escape");
  await expect(page.getByTestId("battle-home").getByTestId("player-photo")).toHaveCount(0);
});
