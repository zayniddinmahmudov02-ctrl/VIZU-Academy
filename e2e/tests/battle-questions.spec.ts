import { expect, test, type Page } from "@playwright/test";

import { ADMIN, createStudent, loginViaForm, PASSWORD, useLanguage } from "./helpers";

// VIZU Battle text questions (2026-11-19) on the local stack: needs the question seed applied to the E2E database
// (python -m app.scripts.battle_questions_seed plan / apply --confirm <id>) besides the picture seed (battle_seed).
// Student: an A1 practice match mixes picture and text rounds; a text round shows the prompt, the format's instruction (German +
// Uzbek), 3–4 options, and after the round the explanation. Admin: statistics per level (≥ 500 active each), filters, a question with
// two correct answers is refused, create → edit → delete, JSON import (check first: valid / duplicate / invalid, then import).

async function noHorizontalScroll(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow, "horizontal scroll").toBeLessThanOrEqual(1);
}

test("student: an A1 match mixes picture rounds and vocabulary / grammar rounds with instruction, options and explanation", async ({ page }) => {
  test.setTimeout(150_000);
  await loginViaForm(page, await createStudent(), PASSWORD); // the login form is German; Uzbek is switched on afterwards
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 20_000 });
  await page.evaluate(() => localStorage.setItem("vizu-language", JSON.stringify({ state: { language: "uz" }, version: 0 })));
  await page.goto("/battle");
  await page.getByTestId("battle-practice").click();
  const arena = page.getByTestId("battle-arena");
  await expect(arena).toBeVisible({ timeout: 20_000 });
  const seen = new Set<string>();
  for (let round = 1; round <= 10 && !(seen.has("text") && seen.has("picture")); round++) {
    await expect(arena).toHaveAttribute("data-round", String(round), { timeout: 20_000 });
    await expect(arena).toHaveAttribute("data-phase", "question", { timeout: 10_000 });
    const card = page.getByTestId("question-card");
    const kind = (await card.getAttribute("data-kind")) ?? "";
    seen.add(kind);
    const options = page.locator('[data-testid^="answer-"]');
    if (kind === "text") {
      await expect(page.getByTestId("question-prompt")).not.toBeEmpty();
      await expect(page.getByTestId("question-instruction")).not.toBeEmpty();
      await expect(card).toContainText(/toping|tanlang|to‘ldiring|yakunlang/); // the Uzbek line of the instruction
      expect([3, 4]).toContain(await options.count());
      await expect(page.getByTestId("question-image")).toHaveCount(0);
      if (!seen.has("text-shot")) {
        await page.screenshot({ path: "test-results/battle-text-round.png" });
        seen.add("text-shot");
      }
    } else {
      await expect(page.getByTestId("question-image")).toBeVisible();
      await expect(options).toHaveCount(4);
    }
    await noHorizontalScroll(page);
    await page.getByTestId("answer-0").click();
    await expect(arena).toHaveAttribute("data-phase", "reveal", { timeout: 15_000 });
    const states = await options.evaluateAll((els) => els.map((e) => e.getAttribute("data-state")));
    expect(states.filter((s) => s === "correct" || s === "missed")).toHaveLength(1); // exactly one correct answer
    if (kind === "text") await expect(page.getByTestId("question-explanation")).toBeVisible();
  }
  expect(seen.has("text")).toBe(true);
  expect(seen.has("picture")).toBe(true);
  page.once("dialog", (d) => d.accept());
  await page.locator('[data-testid="arena-surrender"]:visible, [data-testid="arena-surrender-mobile"]:visible').first().click();
  await expect(page.getByTestId("battle-result")).toBeVisible({ timeout: 10_000 });
});

test.describe("admin", () => {
  test.skip(({ isMobile }) => isMobile, "admin panel, desktop");

  test("Fragen: statistics per level, filters, refused double answer, create / edit / delete, JSON import", async ({ page }) => {
    test.setTimeout(120_000);
    const tag = Date.now().toString(36);
    await useLanguage(page, "de");
    await loginViaForm(page, ADMIN.email, ADMIN.password);
    await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
    await page.getByRole("button", { name: "Bestätigen" }).click();
    await expect(page).toHaveURL(/\/admin/);
    await page.goto("/admin/battle");
    await expect(page.getByTestId("admin-battle-stage-B2")).toContainText("Fragen");
    await page.getByTestId("admin-battle-tab-questions").click();
    for (const lv of ["A1", "A2", "B1", "B2", "C1"]) {
      await expect.poll(async () => Number(await page.getByTestId(`bq-active-${lv}`).textContent()), { timeout: 15_000 }).toBeGreaterThanOrEqual(500);
    }
    await page.getByTestId("bq-filter-level").selectOption("B1");
    await page.getByTestId("bq-filter-kind").selectOption("grammar");
    await expect(page.getByTestId("bq-row").first()).toContainText("B1");
    await expect(page.getByTestId("bq-row").first()).toContainText("Grammatik");

    // two correct answers are refused
    await page.getByTestId("bq-new").click();
    const editor = page.getByTestId("bq-editor");
    await page.getByTestId("bq-edit-level").selectOption("B1");
    await page.getByTestId("bq-edit-format").selectOption("grammar");
    await page.getByTestId("bq-edit-topic").selectOption("passiv");
    await page.getByTestId("bq-edit-prompt").fill(`Der Kuchen ___ gerade gebacken. (${tag})`);
    await page.getByTestId("bq-edit-answer").fill("wird");
    await page.getByTestId("bq-edit-wrong-0").fill("wird");
    await page.getByTestId("bq-edit-wrong-1").fill("hat");
    await page.getByTestId("bq-edit-wrong-2").fill("ist");
    await page.getByTestId("bq-edit-save").click();
    await expect(page.getByTestId("bq-edit-error")).toContainText("BATTLE_QUESTION_INVALID");
    await page.getByTestId("bq-edit-wrong-0").fill("werden");
    await page.getByTestId("bq-edit-save").click();
    await expect(editor).toHaveCount(0);
    await expect(page.getByRole("status")).toContainText("angelegt");

    // find it, publish it, delete it
    await page.getByTestId("bq-filter-kind").selectOption("");
    await page.getByTestId("bq-search").fill(tag);
    await expect(page.getByTestId("bq-row")).toHaveCount(1);
    await page.getByTestId("bq-row").click();
    await page.getByTestId("bq-edit-status").selectOption("published");
    await page.getByTestId("bq-edit-save").click();
    await expect(page.getByRole("status")).toContainText("gespeichert");
    await expect(page.getByTestId("bq-row")).toContainText("published");
    await page.getByTestId("bq-row").click();
    page.once("dialog", (d) => d.accept());
    await page.getByTestId("bq-edit-delete").click();
    await expect(page.getByRole("status")).toContainText("gelöscht");
    await expect(page.getByTestId("bq-row")).toHaveCount(0);

    // import: check first, then import (an existing question counts as duplicate, a broken one is listed)
    await page.getByTestId("bq-import-open").click();
    const items = [
      { level: "A2", format: "grammar", topic: "akk_dat", prompt: `Ich helfe ___ Nachbarn. (${tag})`, answer: "dem", wrong: ["den", "der", "des"] },
      { level: "A2", format: "grammar", topic: "akk_dat", prompt: "Ich gebe ___ Mann das Buch.", answer: "dem", wrong: ["den", "der", "des"] },
      { level: "A2", format: "grammar", topic: "akk_dat", prompt: `Kaputt (${tag}) ___`, answer: "a", wrong: ["a", "b", "c"] },
    ];
    await page.getByTestId("bq-import-text").fill(JSON.stringify(items));
    await page.getByTestId("bq-import-check").click();
    const report = page.getByTestId("bq-import-report");
    await expect(report).toContainText("3 gelesen");
    await expect(report).toContainText("1 gültig");
    await expect(report).toContainText("1 doppelt");
    await expect(report).toContainText("1 fehlerhaft");
    await page.getByTestId("bq-import-apply").click();
    await expect(report).toContainText("1 importiert");
    await page.getByTestId("bq-import").locator("button[aria-label='Schließen']").click();
    await page.getByTestId("bq-filter-level").selectOption(""); // the imported question is A2
    await page.getByTestId("bq-search").fill(tag);
    await expect(page.getByTestId("bq-row")).toHaveCount(1);
    await expect(page.getByTestId("bq-row")).toContainText("draft");
    // clean up the imported question
    await page.getByTestId("bq-row").click();
    page.once("dialog", (d) => d.accept());
    await page.getByTestId("bq-edit-delete").click();
    await expect(page.getByTestId("bq-row")).toHaveCount(0);
  });
});
