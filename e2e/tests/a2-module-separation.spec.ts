import { expect, test, type Page } from "@playwright/test";

import { ADMIN, API_URL, loginViaForm, useLanguage } from "./helpers";

// A2 module separation against the throwaway stack (DB vizu_gcr_e2e): the A2 book edition is imported,
// the Wörterbuch imported and `python -m app.scripts.a2_module_separation apply` has run (the same
// data step as production). gc-student2 owns A2 (approved test order from gcr_e2e_seed.py).
const BUYER = "gc-student2@example.com";
const PASSWORD = "Geheim123!";

async function token(identifier: string, password: string) {
  const res = await fetch(`${API_URL}/api/v1/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ identifier, password }) });
  expect(res.status).toBe(200);
  return (await res.json()).access_token as string;
}

async function lessons(): Promise<Record<number, string>> {
  const auth = { Authorization: `Bearer ${await token(BUYER, PASSWORD)}` };
  const res = await fetch(`${API_URL}/api/v1/lms/levels/A2`, { headers: auth });
  expect(res.status).toBe(200);
  const body = await res.json();
  return Object.fromEntries(body.lessons.map((l: { number: number; id: string }) => [l.number, l.id]));
}

async function noHorizontalScroll(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(1);
}

test.describe("A2 admin: module of every written task, Wortschatz data and CSV", () => {
  test.skip(({ isMobile }) => isMobile, "admin flow runs on desktop");

  test("word list marks missing data, CSV preview writes nothing on an error; writings show their competency", async ({ page }) => {
    const ids = await lessons();
    await useLanguage(page, "de");
    await loginViaForm(page, ADMIN.email, ADMIN.password);
    await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
    await page.getByRole("button", { name: "Bestätigen" }).click();
    await expect(page).toHaveURL(/\/admin/);

    await page.goto(`/admin/lessons/${ids[1]}?tab=wortschatz`);
    const table = page.getByTestId("admin-words");
    await expect(table.getByTestId("word-row")).toHaveCount(60);
    await expect(table.getByTestId("word-missing").filter({ hasText: "Beispiel" }).first()).toBeVisible(); // unmatched words: example missing
    await page.getByTestId("words-import-file").setInputFiles({
      name: "falsch.csv", mimeType: "text/csv", buffer: Buffer.from("german_word,translation,article\nTest,sinov,xyz\n"),
    });
    const report = page.getByTestId("words-import-report");
    await expect(report).toContainText("Vorschau");
    await expect(report).toContainText("line 2");
    await expect(page.getByTestId("words-import-apply")).toHaveCount(0);

    await page.goto(`/admin/lessons/${ids[5]}?tab=writing`);
    await expect(page.getByTestId("writing-competency")).toHaveCount(4);
    const labels = await page.getByTestId("writing-competency").allTextContents();
    expect(labels.sort()).toEqual(["Lesen", "Schreiben", "Schreiben", "Wortschatz"]);
  });
});

test.describe("A2: Wortschatz, Lesen and Schreiben are separate modules", () => {
  let ids: Record<number, string>;

  test.beforeAll(async () => {
    ids = await lessons();
  });

  test.beforeEach(async ({ page }) => {
    await useLanguage(page, "de"); // loginViaForm uses the German labels
    await loginViaForm(page, BUYER, PASSWORD);
    await expect(page).not.toHaveURL(/\/login/);
  });

  test("Schreiben lists only Schreiben tasks — no Lesen questions, no Wortschatz worksheet", async ({ page }) => {
    await page.goto(`/lektion/${ids[5]}/schreiben`);
    const section = page.locator('[data-testid="writing-section"][data-competency="SCHREIBEN"]');
    await expect(section.getByTestId("writing-task").first()).toBeVisible();
    const titles = await section.getByTestId("writing-task").evaluateAll((els) => els.map((e) => e.getAttribute("data-title") ?? ""));
    expect(titles.length).toBe(2);
    for (const title of titles) expect(title).toMatch(/^Schreiben/);
    await expect(page.getByText("Lesen: Fragen zum Text")).toHaveCount(0);
    await expect(page.getByText(/Wortschatz-Aufgabe/)).toHaveCount(0);
    await noHorizontalScroll(page);
  });

  test("Lesen shows its open questions next to the reading test", async ({ page }) => {
    await page.goto(`/lektion/${ids[5]}/lesen`);
    const lesen = page.locator('[data-testid="writing-section"][data-competency="LESEN"]');
    await expect(lesen.getByTestId("writing-task")).toHaveCount(1);
    await expect(lesen.getByTestId("writing-task")).toHaveAttribute("data-title", "Lesen: Fragen zum Text (Aufgabe)");
    await noHorizontalScroll(page);
  });

  test("Grammatik shows its written exercise, not under Schreiben", async ({ page }) => {
    await page.goto(`/lektion/${ids[2]}/grammatik`);
    const g = page.locator('[data-testid="writing-section"][data-competency="GRAMMATIK"]');
    await expect(g.getByTestId("writing-task")).toHaveCount(1);
    await page.goto(`/lektion/${ids[2]}/schreiben`);
    await expect(page.getByText(/Grammatik-Aufgabe/)).toHaveCount(0);
  });

  test("Wortschatz: dictionary search, save / learned, tests and worksheet in their own tabs", async ({ page }) => {
    // desktop and mobile share the student: start from a clean state for every word of the lesson
    const auth = { Authorization: `Bearer ${await token(BUYER, PASSWORD)}`, "Content-Type": "application/json" };
    const list = await (await fetch(`${API_URL}/api/v1/lesson-skills/${ids[1]}/wortschatz/words`, { headers: auth })).json();
    for (const w of list.words.filter((x: { saved: boolean; learned: boolean }) => x.saved || x.learned)) {
      await fetch(`${API_URL}/api/v1/lesson-skills/${ids[1]}/wortschatz/words/${w.id}/state`, { method: "PUT", headers: auth, body: JSON.stringify({ saved: false, learned: false }) });
    }
    await page.goto(`/lektion/${ids[1]}/wortschatz`);
    await expect(page.getByTestId("ws-dictionary")).toBeVisible();
    const words = page.getByTestId("ws-word");
    await expect(words).toHaveCount(60);
    await page.getByTestId("ws-search").fill("arxitektor");
    await expect(words).toHaveCount(1);
    const word = words.first();
    await expect(word).toHaveAttribute("data-word", "Architekt");
    await expect(word).toContainText("Pl. Architekten");
    await word.getByTestId("ws-save").click();
    await expect(word.getByTestId("ws-save")).toHaveAttribute("aria-pressed", "true");
    await word.getByTestId("ws-learned").click();
    await expect(word.getByTestId("ws-learned")).toHaveAttribute("aria-pressed", "true");
    await page.getByTestId("ws-search").fill("");
    await page.getByTestId("ws-only-saved").click();
    await expect(words).toHaveCount(1);
    await page.reload(); // saved / learned come from the server
    await page.getByTestId("ws-only-saved").click();
    await expect(page.getByTestId("ws-word")).toHaveCount(1);
    await noHorizontalScroll(page);

    // only two parts (2026-11-05): Lug'at + Testlar, no word cards / "Bilaman" anywhere
    await expect(page.getByRole("tab")).toHaveText(["Wörterbuch", /^Tests/]);
    await expect(page.getByTestId("lms-flashcards")).toHaveCount(0);
    await expect(page.getByText(/Weiß ich|Bilaman|Wortkarten/)).toHaveCount(0);
    await page.getByTestId("ws-tab-tests").click();
    const sets = page.getByTestId("ws-tests").getByTestId("exercise-set");
    await expect(sets).toHaveCount(7);
    await expect(sets.first()).toContainText("Wortschatz-Test: Bedeutung");

    // a lesson with a worksheet: it is under Wortschatz → Tests now
    await page.goto(`/lektion/${ids[7]}/wortschatz`);
    await page.getByTestId("ws-tab-tests").click();
    const ws = page.locator('[data-testid="writing-section"][data-competency="WORTSCHATZ"]');
    await expect(ws.getByTestId("writing-task")).toHaveAttribute("data-title", "Wortschatz-Aufgabe: 30 schwierige Wörter");
    await noHorizontalScroll(page);
  });

  test("Wortschatz test is graded on the server and the answer key is not in the page before submitting", async ({ page }) => {
    const auth = { Authorization: `Bearer ${await token(BUYER, PASSWORD)}` };
    const res = await fetch(`${API_URL}/api/v1/lesson-skills/${ids[9]}/exercises/wortschatz`, { headers: auth });
    const body = await res.json();
    expect(JSON.stringify(body)).not.toContain("is_correct");
    const artikel = body.exercises.find((e: { title: string }) => e.title === "Wortschatz-Test: Artikel");
    const start = await fetch(`${API_URL}/api/v1/lesson-skills/${ids[9]}/exercises/wortschatz/${artikel.id}/start`, { method: "POST", headers: auth });
    const attempt = await start.json();
    const answers: Record<string, string> = {};
    for (const q of artikel.questions) {
      const word = q.question.replace("___ ", "");
      const correct = { Vorteil: "der", Nachteil: "der", Meinung: "die", Medien: "die", Nachrichten: "die", Quellen: "die" }[word as string];
      answers[q.id] = q.options.find((o: { text: string }) => o.text === correct).id;
    }
    const submit = await fetch(`${API_URL}/api/v1/lesson-skills/${ids[9]}/exercises/wortschatz/${artikel.id}/submit`, {
      method: "POST", headers: { ...auth, "Content-Type": "application/json" }, body: JSON.stringify({ attempt_id: attempt.id, answers }),
    });
    const result = await submit.json();
    expect(result.score).toBe(100);
    await page.goto(`/lektion/${ids[9]}/wortschatz`);
    await page.getByTestId("ws-tab-tests").click();
    await expect(page.getByTestId("ws-tests")).toContainText("100");
  });
});
