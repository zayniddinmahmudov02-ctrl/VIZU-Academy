import { expect, test, type Page } from "@playwright/test";

import { ADMIN, API_URL, loginViaForm, useLanguage } from "./helpers";

// A2 1–13 after the audio processing, against the throwaway stack (DB vizu_gcr_e2e): the book edition
// imported, every Hören task with its book audio (D:\vz_tmp\work\a2p_local_setup.py), then
// `python -m app.scripts.a2_audio_processing apply`. gc-student2 owns A2 (approved test order, a2l4_e2e_seed.py).
const BUYER = "gc-student2@example.com";
const PASSWORD = "Geheim123!";
// lesson -> published Hören tasks after processing (6: open questions "Prüfung nötig"; 13: wrong audio)
const EXPECTED: Record<number, number> = { 1: 1, 2: 1, 3: 1, 4: 3, 5: 1, 6: 0, 7: 1, 8: 1, 9: 1, 10: 4, 11: 4, 12: 4, 13: 0 };
const L3_KEYS = ["Richtig", "Falsch", "Richtig", "Richtig", "Falsch", "Richtig", "Richtig", "Richtig"];

async function token(identifier: string, password: string) {
  const res = await fetch(`${API_URL}/api/v1/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ identifier, password }) });
  expect(res.status).toBe(200);
  return (await res.json()).access_token as string;
}

async function a2LessonIds(): Promise<Record<number, string>> {
  const admin = await token(ADMIN.email, ADMIN.password);
  const tree = await (await fetch(`${API_URL}/api/v1/admin/media-management/tree`, { headers: { Authorization: `Bearer ${admin}` } })).json();
  const a2 = tree.find((l: { level: string }) => l.level === "A2");
  return Object.fromEntries(a2.modules[0].lessons.map((l: { number: number; id: string }) => [l.number, l.id]));
}

async function noHorizontalScroll(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
}

test.describe.serial("A2 1–13 after the audio processing", () => {
  test("student: every lesson opens and shows exactly the published Hören tasks with players", async ({ page }) => {
    const ids = await a2LessonIds();
    await useLanguage(page, "de");
    await loginViaForm(page, BUYER, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);
    for (let n = 1; n <= 13; n++) {
      await page.goto(`/lektion/${ids[n]}/hoeren`);
      if (EXPECTED[n] === 0) {
        // nothing published: the competency says it has no content yet (and does not count for the lesson)
        await expect(page.getByText(/noch keine Inhalte|noch nicht hochgeladen|keine Hören/), `lesson ${n}`).toBeVisible({ timeout: 20_000 });
        await expect(page.getByTestId("hoeren-task")).toHaveCount(0);
      } else {
        await expect(page.getByTestId("hoeren-task"), `lesson ${n}`).toHaveCount(EXPECTED[n], { timeout: 20_000 });
        // one player per audio file (lesson 7: Text 1 + Text 2)
        await expect(page.getByTestId("hoeren-task").first().locator("audio")).toHaveCount(n === 7 ? 2 : 1, { timeout: 20_000 });
      }
      await expect(page.locator("body")).not.toContainText("Mannsberg — ");
      await noHorizontalScroll(page);
    }
    // lesson 4: the three Texts, audio only — the transcript is there right away
    await page.goto(`/lektion/${ids[4]}/hoeren`);
    await expect(page.getByTestId("hoeren-task")).toHaveText([/Text 1/, /Text 2/, /Text 3/], { timeout: 20_000 });
    await expect(page.getByTestId("hoeren-transcript")).toHaveCount(3);
    await expect(page.locator("body")).not.toContainText("Familie Mannsberg");
  });

  test("student: lesson 3 Hören test — graded on the server, result and progress kept", async ({ page, isMobile }) => {
    test.skip(isMobile, "the attempt is written once (desktop); mobile checks the layout above");
    const ids = await a2LessonIds();
    await useLanguage(page, "de");
    await loginViaForm(page, BUYER, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);
    await page.goto(`/lektion/${ids[3]}/hoeren`);
    const task = page.getByTestId("hoeren-task");
    await expect(task.getByTestId("test-question")).toHaveCount(8, { timeout: 20_000 });
    const section = await (await fetch(`${API_URL}/api/v1/lesson-skills/${ids[3]}/hoeren`, {
      headers: { Authorization: `Bearer ${await token(BUYER, PASSWORD)}` },
    })).json();
    if (section.tasks[0].summary.attempts_count === 0) {
      await expect(task.getByTestId("hoeren-transcript")).toHaveCount(0); // the transcript only after the first attempt
    }
    const questions = task.getByTestId("test-question");
    await expect(questions).toHaveCount(8);
    for (let i = 0; i < 8; i++) {
      await questions.nth(i).getByTestId("test-option").filter({ hasText: new RegExp(`^${L3_KEYS[i]}$`) }).click();
    }
    await task.getByTestId("test-check").click();
    await expect(task.getByTestId("test-result")).toContainText("100", { timeout: 20_000 });
    await expect(questions.and(page.locator('[data-result="correct"]'))).toHaveCount(8);
    await expect(task.getByTestId("hoeren-transcript")).toBeVisible();
    await page.reload();
    await expect(page.getByTestId("hoeren-task").getByTestId("hoeren-transcript")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByTestId("hoeren-task")).toContainText("100"); // best score kept
  });

  test("admin: processing overview with progress, transcript, keys and the open problems", async ({ page }) => {
    await useLanguage(page, "de");
    await loginViaForm(page, ADMIN.email, ADMIN.password);
    await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
    await page.getByRole("button", { name: "Bestätigen" }).click();
    await expect(page).toHaveURL(/\/admin/);
    await page.goto("/admin/media-management");
    await page.getByTestId("mm-level").selectOption("A2");
    const panel = page.getByTestId("a2-audio-processing");
    await expect(panel.getByTestId("a2p-summary")).toContainText("22/27", { timeout: 20_000 });
    await expect(panel.getByTestId("a2p-lesson")).toHaveCount(13);
    const l13 = panel.locator('[data-testid="a2p-lesson"][data-lesson="13"]');
    await l13.getByRole("button").first().click();
    await expect(l13.getByTestId("a2p-task")).toHaveCount(4);
    await expect(l13.getByTestId("a2p-task").first()).toHaveAttribute("data-status", "NEEDS_REVIEW");
    await expect(l13.getByTestId("a2p-problems").first()).toContainText("byte-identisch");
    const l2 = panel.locator('[data-testid="a2p-lesson"][data-lesson="2"]');
    await l2.getByRole("button").first().click();
    await l2.getByTestId("a2p-task").getByRole("button").first().click();
    await expect(l2.getByTestId("a2p-transcript")).toContainText("Professor Müller");
    await expect(l2.getByTestId("a2p-transcript")).toContainText("[unverständlich]");
    await expect(l2.getByTestId("a2p-question")).toHaveCount(12);
    await expect(l2.getByTestId("a2p-question").first()).toContainText("geprüft");
    await noHorizontalScroll(page);
  });
});
