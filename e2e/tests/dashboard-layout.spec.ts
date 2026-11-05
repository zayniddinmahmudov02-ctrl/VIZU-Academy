import { expect, test, type Page } from "@playwright/test";

import { createStudent, loginViaForm, PASSWORD, useLanguage } from "./helpers";

// Dashboard order (2026-11-05): welcome → compact Werbung banner → Lernwerkzeuge → ONE collapsible "A1–C1 Kurse" frame
// → compact Lernserie; no Erfolge / Zertifikate cards. Checked at the brief's viewports. Local stack only.

async function login(page: Page) {
  const email = await createStudent();
  await useLanguage(page, "de");
  await loginViaForm(page, email, PASSWORD);
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 20_000 });
}

const top = async (page: Page, id: string) => (await page.getByTestId(id).first().boundingBox())!.y;

test("order, compact banner, one course frame, expand/collapse, links, stats", async ({ page, isMobile }) => {
  await login(page);
  await expect(page.getByTestId("dashboard-course")).toHaveCount(5);

  const order = ["dashboard-welcome", "dashboard-ad", "dashboard-learning-tools", "dashboard-courses", "dashboard-stats"];
  const ys = [];
  for (const id of order) ys.push(await top(page, id));
  expect(ys).toEqual([...ys].sort((a, b) => a - b));
  await expect(page.getByTestId("dashboard-achievements")).toHaveCount(0);
  await expect(page.getByTestId("dashboard-certificates")).toHaveCount(0);

  // compact banner: one link with a CTA; desktop height ~156 px (was 220), phone well under half the screen
  const ad = page.getByTestId("dashboard-ad").locator("a").first();
  await expect(ad).toBeVisible();
  expect(await ad.getAttribute("href")).toBeTruthy();
  const adBox = (await ad.boundingBox())!;
  if (isMobile) expect(adBox.height).toBeLessThan(page.viewportSize()!.height * 0.45);
  else expect(adBox.height).toBeLessThanOrEqual(175);

  // all five levels inside the single frame, tiles without their own shadow/frame
  const frame = page.getByTestId("dashboard-courses");
  await expect(frame.getByRole("heading", { name: /A1–C1 Kurse/ })).toBeVisible();
  await expect(frame).toContainText("Wähle dein Deutschniveau.");
  await expect(page.getByTestId("dashboard-courses-count")).toHaveText("5 Kurse");
  await expect(frame.getByTestId("dashboard-course")).toHaveCount(5);
  expect(await frame.getByTestId("dashboard-course").evaluateAll((els) => els.map((e) => getComputedStyle(e).boxShadow))).toEqual(Array(5).fill("none"));
  for (const level of ["A1", "A2", "B1", "B2", "C1"]) await expect(frame.locator(`[data-level="${level}"]`)).toHaveCount(1);
  if (!isMobile) {
    const rows = new Set(await frame.getByTestId("dashboard-course").evaluateAll((els) => els.map((e) => Math.round(e.getBoundingClientRect().top))));
    if (page.viewportSize()!.width >= 1280) expect(rows.size).toBe(1); // xl: one row
  }

  // open by default → collapse → expand
  const toggle = page.getByTestId("dashboard-courses-toggle");
  await expect(toggle).toHaveAttribute("aria-expanded", "true");
  await toggle.click();
  await expect(toggle).toHaveAttribute("aria-expanded", "false");
  await expect(page.getByTestId("dashboard-courses-panel")).toHaveCount(0);
  await toggle.click();
  await expect(toggle).toHaveAttribute("aria-expanded", "true");
  await expect(frame.getByTestId("dashboard-course")).toHaveCount(5);

  // course links keep working (header link of A1 opens its course page)
  await frame.locator('[data-level="A1"]').getByRole("link", { name: "Kurs A1 öffnen" }).click();
  await expect(page).toHaveURL(/\/kurse\/a1/i);
  await page.goBack();

  // compact Lernserie: four facts
  const stats = page.getByTestId("dashboard-streak");
  await expect(stats).toContainText("Aktuelle Serie");
  await expect(stats).toContainText("Lerntage (letzte 7 Tage)");
  await expect(stats).toContainText("Lernzeit gesamt");
  await expect(stats).toContainText("Letzte Aktivität");
  expect((await stats.boundingBox())!.height).toBeLessThan(isMobile ? 220 : 140);
});

for (const vp of [
  { width: 1920, height: 1080 }, { width: 1440, height: 900 }, { width: 1366, height: 768 },
  { width: 820, height: 1180 }, { width: 390, height: 844 }, { width: 360, height: 800 },
]) {
  test(`no horizontal overflow and banner on top at ${vp.width}×${vp.height}`, async ({ page, isMobile }) => {
    test.skip(isMobile, "viewport sweep runs once (desktop project)");
    await page.setViewportSize(vp);
    await login(page);
    await expect(page.getByTestId("dashboard-course")).toHaveCount(5);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(1);
    expect(await top(page, "dashboard-ad")).toBeLessThan(vp.height); // banner visible on arrival
    expect(await top(page, "dashboard-ad")).toBeLessThan(await top(page, "dashboard-learning-tools"));
    await expect(page.getByTestId("dashboard-courses-toggle")).toBeVisible();
    const tb = (await page.getByTestId("dashboard-courses-toggle").boundingBox())!;
    expect(tb.height).toBeGreaterThanOrEqual(44); // easy to tap
    // no clipped button text (Battle CTA, banner CTA)
    for (const id of ["battle-banner-cta"]) {
      const clipped = await page.getByTestId(id).evaluate((el) => el.scrollWidth > el.clientWidth + 1);
      expect(clipped, `${id} text clipped`).toBe(false);
    }
    const adBox = (await page.getByTestId("dashboard-ad").boundingBox())!;
    expect(adBox.height).toBeLessThanOrEqual(vp.width < 640 ? 190 : 175);
    if (process.env.E2E_SHOTS) await page.screenshot({ path: `${process.env.E2E_SHOTS}/dashboard-${vp.width}.png`, fullPage: true });
  });
}
