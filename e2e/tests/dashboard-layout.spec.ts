import { expect, test, type Page } from "@playwright/test";

import { createStudent, loginViaForm, PASSWORD, useLanguage } from "./helpers";

// Dashboard order (2026-11-15): welcome → compact Werbung banner → hub with the main cards → Lernwerkzeuge → compact Lernserie;
// the A1–C1 levels are no longer separate buttons here (they live behind "A1–C1 Kurse"); no Erfolge / Zertifikate cards.
// 2026-11-25 (owner): quick buttons "Mein Lehrer/in" (My Teacher) and "Wörterbuch / Lug'at" in the welcome header (right on wide screens,
// no extra height: the hub stays one row of five on xl); the Wörterbuch is no longer a card of the Lernwerkzeuge row.
// Checked at the brief's viewports. Local stack only.

async function login(page: Page) {
  const email = await createStudent();
  await useLanguage(page, "de");
  await loginViaForm(page, email, PASSWORD);
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 20_000 });
}

const top = async (page: Page, id: string) => (await page.getByTestId(id).first().boundingBox())!.y;
const CARDS = ["courses", "media", "prep", "certificates", "purchase"];

test("order, compact banner, five hub cards (no level buttons), quick buttons, links, stats", async ({ page, isMobile }) => {
  await login(page);
  const hub = page.getByTestId("dashboard-hub");
  await expect(hub.getByTestId("hub-card")).toHaveCount(CARDS.length);
  expect(await hub.getByTestId("hub-card").evaluateAll((els) => els.map((e) => e.getAttribute("data-card")))).toEqual(CARDS);

  const order = ["dashboard-welcome", "dashboard-ad", "dashboard-hub", "dashboard-learning-tools", "dashboard-stats"];
  const ys = [];
  for (const id of order) ys.push(await top(page, id));
  expect(ys).toEqual([...ys].sort((a, b) => a - b));
  await expect(page.getByTestId("dashboard-achievements")).toHaveCount(0);
  await expect(page.getByTestId("dashboard-certificates")).toHaveCount(0);
  // the old per-level frame is gone: no A1/A2/B1/B2/C1 buttons on the dashboard
  await expect(page.getByTestId("dashboard-courses")).toHaveCount(0);
  await expect(page.getByTestId("dashboard-course")).toHaveCount(0);
  for (const level of ["A1", "A2", "B1", "B2", "C1"]) await expect(page.locator(`main [data-level="${level}"]`)).toHaveCount(0);

  // compact banner: one link with a CTA; desktop height ~156 px (was 220), phone well under half the screen
  const ad = page.getByTestId("dashboard-ad").locator("a").first();
  await expect(ad).toBeVisible();
  expect(await ad.getAttribute("href")).toBeTruthy();
  const adBox = (await ad.boundingBox())!;
  if (isMobile) expect(adBox.height).toBeLessThan(page.viewportSize()!.height * 0.45);
  else expect(adBox.height).toBeLessThanOrEqual(175);

  // hub: names, descriptions and targets (German)
  const card = (id: string) => hub.locator(`[data-card="${id}"]`);
  await expect(card("courses")).toContainText("A1–C1 Kurse");
  await expect(card("media")).toContainText("Medien");
  await expect(card("media")).toContainText("Bibliothek, Musik und Filme entdecken");
  await expect(card("prep")).toContainText("Vorbereitung");
  await expect(card("certificates")).toContainText("Zertifikate");
  await expect(card("certificates")).toContainText("Erfolge und Zertifikate ansehen");
  await expect(card("purchase")).toContainText("Angebote");
  for (const [id, href] of [["courses", "/kurse"], ["media", "/medien"], ["prep", "/vorbereitung"], ["certificates", "/certificates"], ["purchase", "/angebote"]]) {
    await expect(card(id)).toHaveAttribute("href", href);
  }
  if (!isMobile && page.viewportSize()!.width >= 1280) {
    await page.mouse.move(2, 2); // the login click leaves the pointer somewhere: a hovered card is lifted by 4 px
    // xl: one row of five — polled, the cards slide in with a staggered entrance animation first
    await expect.poll(async () => new Set(await hub.getByTestId("hub-card").evaluateAll((els) => els.map((e) => Math.round(e.getBoundingClientRect().top)))).size, { timeout: 5_000 }).toBe(1);
  }
  // quick buttons in the welcome header: Mein Lehrer/in + Wörterbuch (Lug'at); the Wörterbuch is no second link in the tools row
  const quick = (id: string) => page.getByTestId("dashboard-welcome").locator(`[data-testid="quick-link"][data-link="${id}"]`);
  await expect(quick("my-teacher")).toHaveText("Mein Lehrer/in");
  await expect(quick("my-teacher")).toHaveAttribute("href", "/my-teacher");
  await expect(quick("dictionary")).toHaveText("Wörterbuch");
  await expect(quick("dictionary")).toHaveAttribute("href", "/woerterbuch");
  await expect(page.getByTestId("dashboard-learning-tools").locator('a[href="/woerterbuch"]')).toHaveCount(0);
  if (!isMobile) {
    // on wide screens they sit beside the greeting: the welcome header is not taller than the buttons + text
    const welcome = (await page.getByTestId("dashboard-welcome").boundingBox())!;
    expect(welcome.height).toBeLessThan(90);
  }
  await quick("my-teacher").click();
  await expect(page).toHaveURL(/\/my-teacher$/);
  await page.goto("/dashboard");
  await quick("dictionary").click();
  await expect(page).toHaveURL(/\/woerterbuch$/);
  await page.goto("/dashboard");

  // old course links keep working
  await page.goto("/kurse/a1");
  await expect(page).toHaveURL(/\/kurse\/a1/i);
  await page.goto("/dashboard");

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
    await expect(page.getByTestId("hub-card")).toHaveCount(CARDS.length);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(1);
    expect(await top(page, "dashboard-ad")).toBeLessThan(vp.height); // banner visible on arrival
    expect(await top(page, "dashboard-ad")).toBeLessThan(await top(page, "dashboard-hub"));
    expect(await top(page, "dashboard-hub")).toBeLessThan(await top(page, "dashboard-learning-tools"));
    // every hub card is easy to tap and none is clipped
    for (const box of await page.getByTestId("hub-card").evaluateAll((els) => els.map((e) => ({ h: e.getBoundingClientRect().height, clipped: e.scrollWidth > e.clientWidth + 1 })))) {
      expect(box.h).toBeGreaterThanOrEqual(44);
      expect(box.clipped).toBe(false);
    }
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