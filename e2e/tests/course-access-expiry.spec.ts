import { expect, test } from "@playwright/test";

import { API_URL, PASSWORD, apiToken, loginViaForm, useLanguage } from "./helpers";

// Bought course whose access period is over (owner 2026-11-25: keep the time limit, but say so and offer to renew).
// Needs the seed D:\vz_tmp\work\exp_e2e_seed.py on vizu_gcr_e2e: exp-expired@example.com (A2 order ended 10 days ago),
// exp-active@example.com (A2 order runs 25 more days). The local E2E database has 13 published A2 lessons. Local stack only.

const EXPIRED = "exp-expired@example.com";
const ACTIVE = "exp-active@example.com";
const DATE = /\d{2}\.\d{2}\.\d{4}/;

async function a2(email: string) {
  const res = await fetch(`${API_URL}/api/v1/lms/levels/A2`, { headers: { Authorization: `Bearer ${await apiToken(email, PASSWORD)}` } });
  expect(res.status).toBe(200);
  return res.json();
}

test.describe("course access expiry", () => {
  test("API: expired order -> expired_at, lessons 2+ stay closed; active -> access_until", async () => {
    const expired = await a2(EXPIRED);
    expect(expired.sale.owned).toBe(false);
    expect(expired.sale.expired_at).toBeTruthy();
    expect(expired.sale.access_until).toBeNull();
    expect(expired.lessons[1].lock_reason).toBe("PREMIUM_REQUIRED");
    const active = await a2(ACTIVE);
    expect(active.sale.owned).toBe(true);
    expect(active.sale.access_until).toBeTruthy();
    expect(active.sale.expired_at).toBeNull();
    expect(active.lessons[1].lock_reason).toBeNull();
  });

  test("expired: card, level page and buy sheet say so and offer to renew (uz)", async ({ page }, info) => {
    await loginViaForm(page, EXPIRED, PASSWORD); // the login form helper reads the German placeholders
    await expect(page).toHaveURL(/\/dashboard/);
    await page.evaluate(() => localStorage.setItem("vizu-language", JSON.stringify({ state: { language: "uz" }, version: 0 })));
    await page.goto("/kurse");
    const card = page.locator('[data-testid="lms-level-card"][data-level="A2"]');
    await expect(card).toHaveAttribute("data-status", "EXPIRED");
    await expect(card.getByTestId("lms-level-status")).toHaveText("Muddati tugagan");
    await expect(card.getByTestId("lms-level-expired")).toContainText("Kursga kirish muddatingiz");
    await expect(card.getByTestId("lms-level-expired")).toContainText(DATE);
    await expect(card.getByTestId("lms-level-renew")).toHaveAttribute("href", /\/angebote/);
    await expect(card.getByTestId("lms-level-renew")).toHaveText(/Uzaytirish/);
    expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
    await page.screenshot({ path: `test-results/expiry-card-${info.project.name}.png`, fullPage: false });

    await page.goto("/kurse/a2");
    await expect(page.getByTestId("lms-level-expired")).toContainText(DATE);
    await expect(page.getByTestId("lms-level-buy")).toHaveText(/Uzaytirish/);
    const cards = page.getByTestId("lms-lesson-card");
    await expect(cards.nth(1)).toHaveAttribute("data-status", "locked");
    await cards.nth(1).click();
    const sheet = page.getByTestId("lms-purchase-modal");
    await expect(sheet.getByTestId("lms-purchase-title")).toHaveText("Kirish muddati tugadi");
    await expect(sheet.getByTestId("lms-purchase-expired")).toContainText("natijalaringiz saqlanib qoladi");
    await expect(sheet.getByTestId("lms-purchase-text")).toHaveCount(0);
    await expect(sheet.getByTestId("lms-purchase-buy")).toHaveText(/Uzaytirish/);
    await page.screenshot({ path: `test-results/expiry-sheet-${info.project.name}.png`, fullPage: false });
    expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
  });

  test("active: card and level page show until when (de)", async ({ page }) => {
    await useLanguage(page, "de");
    await loginViaForm(page, ACTIVE, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);
    await page.goto("/kurse");
    const card = page.locator('[data-testid="lms-level-card"][data-level="A2"]');
    await expect(card).toHaveAttribute("data-status", "ACTIVE");
    await expect(card.getByTestId("lms-level-access-until")).toHaveText(/^Zugang bis \d{2}\.\d{2}\.\d{4}$/);
    await expect(card.getByTestId("lms-level-renew")).toHaveCount(0);
    await page.goto("/kurse/a2");
    await expect(page.getByTestId("lms-level-access-until")).toContainText("Zugang bis");
    await expect(page.getByTestId("lms-level-expired")).toHaveCount(0);
    await expect(page.getByTestId("lms-lesson-card").nth(1)).not.toHaveAttribute("data-status", "locked");
  });
});
