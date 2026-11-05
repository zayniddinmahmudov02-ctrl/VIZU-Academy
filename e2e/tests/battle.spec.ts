import { expect, test, type Browser, type Page } from "@playwright/test";

import { ADMIN, createStudent, loginViaForm, PASSWORD, useLanguage } from "./helpers";

// VIZU DEUTSCH BATTLE on the local stack: needs the battle seed applied to the E2E database
// (python -m app.scripts.battle_seed plan / apply --confirm <id>).

async function student(page: Page) {
  await useLanguage(page, "de");
  await loginViaForm(page, await createStudent(), PASSWORD);
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 20_000 });
}

async function noHorizontalScroll(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow, "horizontal scroll").toBeLessThanOrEqual(1);
}

async function newStudentPage(browser: Browser) {
  const ctx = await browser.newContext({ viewport: { width: 1366, height: 768 } });
  const page = await ctx.newPage();
  await student(page);
  return page;
}

test.describe("Battle — student", () => {
  test("home shows hero, progress, stats, leaderboard and the German stage road", async ({ page }) => {
    await student(page);
    await page.goto("/battle");
    const home = page.getByTestId("battle-home");
    await expect(home).toBeVisible({ timeout: 20_000 });
    await expect(home).toContainText("Sieh das Bild. Finde das Wort. Gewinne den Kampf!");
    await expect(page.getByTestId("battle-start")).toBeEnabled();
    for (const id of ["battle-progress", "battle-stats", "battle-leaderboard-preview", "battle-recent", "battle-achievements", "battle-ladder"]) {
      await expect(page.getByTestId(id)).toBeVisible();
    }
    await expect(page.getByTestId("battle-ladder")).toContainText("Neuschwanstein");
    await expect(page.getByTestId("battle-not-playable")).toHaveCount(0);
    await noHorizontalScroll(page);

    await page.getByTestId("battle-change-avatar").click();
    await expect(page.getByTestId("avatar-picker")).toBeVisible();
    await expect(page.getByTestId("avatar-legend")).toBeDisabled();
    await page.keyboard.press("Escape");
    await expect(page.getByTestId("avatar-picker")).toHaveCount(0);
  });

  test("practice against the bot: picture, four options, server feedback, surrender", async ({ page }) => {
    test.setTimeout(90_000);
    await student(page);
    await page.goto("/battle");
    await page.getByTestId("battle-practice").click();
    await expect(page).toHaveURL(/\/battle\/match\//);
    await expect(page.getByTestId("battle-countdown")).toBeVisible();
    const arena = page.getByTestId("battle-arena");
    await expect(arena).toBeVisible({ timeout: 15_000 });
    await expect(arena).toHaveAttribute("data-round", "1");
    await expect(page.getByTestId("question-image")).toBeVisible();
    await expect(page.locator('[data-testid^="answer-"]')).toHaveCount(4);
    await noHorizontalScroll(page);

    await page.getByTestId("answer-0").click();
    await expect(arena).toHaveAttribute("data-phase", "reveal", { timeout: 15_000 });
    await expect(page.getByTestId("question-feedback")).toBeVisible();
    await expect(page.getByTestId("question-translation")).toBeVisible();
    const states = await page.locator('[data-testid^="answer-"]').evaluateAll((els) => els.map((e) => e.getAttribute("data-state")));
    expect(states.filter((s) => s === "correct" || s === "missed")).toHaveLength(1);

    await expect(arena).toHaveAttribute("data-round", "2", { timeout: 15_000 });
    page.once("dialog", (d) => d.accept());
    await page.locator('[data-testid="arena-surrender"]:visible, [data-testid="arena-surrender-mobile"]:visible').first().click();
    const result = page.getByTestId("battle-result");
    await expect(result).toBeVisible({ timeout: 10_000 });
    await expect(result).toHaveAttribute("data-outcome", "loss");
    await expect(result).toContainText("keine Battle Points");
  });
});

test.describe("Battle — two players", () => {
  test.skip(({ isMobile }) => isMobile, "two browser contexts, desktop only");

  test("ranked: same stage players meet, both answer, the winner gets Battle Points", async ({ browser }) => {
    test.setTimeout(120_000);
    const a = await newStudentPage(browser);
    const b = await newStudentPage(browser);
    await a.goto("/battle");
    await a.getByTestId("battle-start").click();
    await expect(a.getByTestId("battle-matchmaking")).toBeVisible({ timeout: 15_000 });
    await b.goto("/battle");
    await b.getByTestId("battle-start").click();
    for (const p of [a, b]) await expect(p.getByTestId("battle-arena")).toBeVisible({ timeout: 20_000 });
    expect(a.url()).toBe(b.url());

    await a.getByTestId("answer-1").click();
    await expect(b.locator('[data-testid="arena-opponent"]:visible')).toContainText("Gegner hat geantwortet", { timeout: 5_000 });
    await b.getByTestId("answer-2").click();
    for (const p of [a, b]) await expect(p.getByTestId("battle-arena")).toHaveAttribute("data-phase", "reveal", { timeout: 10_000 });

    b.once("dialog", (d) => d.accept());
    await b.getByTestId("arena-surrender").click();
    await expect(b.getByTestId("battle-result")).toHaveAttribute("data-outcome", "loss", { timeout: 10_000 });
    await expect(a.getByTestId("battle-result")).toHaveAttribute("data-outcome", "win", { timeout: 10_000 });
    await expect(a.getByTestId("result-points")).toContainText("+25 BP", { timeout: 5_000 });
    await a.context().close();
    await b.context().close();
  });

  test("private room: code, join, countdown", async ({ browser }) => {
    test.setTimeout(90_000);
    const a = await newStudentPage(browser);
    const b = await newStudentPage(browser);
    await a.goto("/battle");
    await a.getByTestId("battle-create-room").click();
    const code = (await a.getByTestId("lobby-room-code").textContent({ timeout: 15_000 }))?.trim() ?? "";
    expect(code).toMatch(/^[A-Z0-9]{6}$/);
    await b.goto("/battle");
    await b.getByTestId("battle-room-code").fill(code);
    await b.getByTestId("battle-join-room").click();
    for (const p of [a, b]) await expect(p.getByTestId("battle-countdown").or(p.getByTestId("battle-arena"))).toBeVisible({ timeout: 15_000 });
    for (const p of [a, b]) {
      p.once("dialog", (d) => d.accept());
    }
    await expect(a.getByTestId("battle-arena")).toBeVisible({ timeout: 15_000 });
    await a.getByTestId("arena-surrender").click();
    await expect(b.getByTestId("battle-result")).toHaveAttribute("data-outcome", "win", { timeout: 10_000 });
    await a.context().close();
    await b.context().close();
  });
});

test.describe("Battle — admin", () => {
  test("Game Management: overview, words with pictures, theme draft preview and publish", async ({ page }) => {
    test.setTimeout(90_000);
    await useLanguage(page, "de");
    await loginViaForm(page, ADMIN.email, ADMIN.password);
    await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
    await page.getByRole("button", { name: "Bestätigen" }).click();
    await expect(page).toHaveURL(/\/admin/);
    await page.goto("/admin/battle");
    await expect(page.getByTestId("admin-battle-overview")).toContainText("A1");

    await page.getByTestId("admin-battle-tab-words").click();
    await expect(page.getByTestId("admin-battle-word").first()).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("admin-battle-word").first().click();
    await expect(page.getByTestId("admin-battle-drawer")).toContainText("Lizenz");
    await page.keyboard.press("Escape");
    await page.getByTestId("admin-battle-drawer").locator("button[aria-label='Schließen']").click();

    await page.getByTestId("admin-battle-tab-themes").click();
    await page.getByTestId("admin-theme-B2").click();
    await expect(page.getByTestId("admin-theme-preview-desktop")).toBeVisible();
    await expect(page.getByTestId("admin-theme-preview-mobile")).toBeVisible();
    await page.getByTestId("admin-theme-save").click();
    await expect(page.getByRole("status")).toContainText("Entwurf gespeichert");
    await page.getByTestId("admin-theme-publish").click();
    await expect(page.getByRole("status")).toContainText("veröffentlicht");
  });
});
