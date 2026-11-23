import { expect, test, type Page } from "@playwright/test";

import { ADMIN, API_URL, PASSWORD, apiToken, createStudent, grantMultilevelPremium, loginViaForm } from "./helpers";

// Multilevel Modelltest → Lesen answer keys (owner's PDF "Antworten.pdf"). Local stack only. The admin imports the Lesen keys of Modelltest 6 through
// the Answer Key tool (Teil 1 order A–E, Teil 3 headings A–J, Teil 4 a / b / c), then a student's sheet is scored by the server against exactly that key.
// Only Modelltest 6 gets its keys here: multilevel-open-tests.spec.ts needs a Modelltest of 2–5 WITHOUT Lesen keys in the local DB.
// (Production: all six through `python -m app.scripts.multilevel_lesen_keys`.)
const MT6 = "1-a, 2-b, 3-c, 4-d, 5-e\n6-b, 7-b, 8-b, 9-c, 10-c\n11-f, 12-a, 13-c, 14-e, 15-d, 16-i, 17-j\n18-b, 19-a, 20-a, 21-b, 22-a, 23-b, 24-a, 25-b, 26-b, 27-a\n28-b, 29-b, 30-b, 31-c, 32-b, 33-b, 34-c, 35-b";
const LETTERS = [...MT6.matchAll(/\d+-([a-j])/g)].map((m) => m[1]);

const call = async (method: string, url: string, bearer: string | null, body?: unknown) => {
  const res = await fetch(`${API_URL}/api/v1${url}`, { method, headers: { ...(bearer ? { Authorization: `Bearer ${bearer}` } : {}), ...(body ? { "Content-Type": "application/json" } : {}) }, body: body ? JSON.stringify(body) : undefined });
  const text = await res.text();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return { status: res.status, text, json: (text && res.headers.get("content-type")?.includes("json") ? JSON.parse(text) : null) as any };
};

async function adminLogin(page: Page) {
  await page.addInitScript(() => localStorage.setItem("vizu-language", JSON.stringify({ state: { language: "de" }, version: 0 })));
  await loginViaForm(page, ADMIN.email, ADMIN.password);
  await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
  await page.getByRole("button", { name: "Bestätigen" }).click();
  await expect(page).toHaveURL(/\/admin/);
}

test.describe.serial("Multilevel Lesen answer keys", () => {
  test.skip(({ isMobile }) => isMobile, "admin tool + API checks run on desktop");
  let admin = "";
  let mt6 = "";
  let oldStatus = "";

  test.beforeAll(async () => {
    expect(LETTERS).toHaveLength(35);
    admin = await apiToken(ADMIN.email, ADMIN.password);
    const overview = (await call("GET", "/admin/multilevel-audio", admin)).json as { tests: { model_test_id: string; sort_order: number }[] };
    mt6 = overview.tests.find((t) => t.sort_order === 6)!.model_test_id;
    const all = (await call("GET", "/mock-exam/model-tests", admin)).json as { id: string; status: string }[];
    oldStatus = all.find((t) => t.id === mt6)!.status;
    if (oldStatus !== "PUBLISHED") expect((await call("PUT", `/mock-exam/model-tests/${mt6}`, admin, { status: "PUBLISHED" })).status).toBe(200);
  });

  test.afterAll(async () => {
    if (oldStatus && oldStatus !== "PUBLISHED") await call("PUT", `/mock-exam/model-tests/${mt6}`, admin, { status: oldStatus });
  });

  test("admin: Lesen keys of Modelltest 6 imported (35), order A–E, headings A–J and true / false c accepted", async ({ page }) => {
    await adminLogin(page);
    await page.goto("/admin/mock-exams/multilevel");
    await expect(page.getByTestId("keys-card")).toBeVisible({ timeout: 30_000 });
    const select = page.getByTestId("keys-test");
    const options = await select.locator("option").allTextContents();
    await select.selectOption({ label: options[5] });
    await page.getByTestId("keys-section-LESEN").click();
    await expect(page.getByTestId("keys-summary")).toContainText("Modelltest 6 · Lesen");
    await expect(page.getByTestId("key-row")).toHaveCount(35);

    await page.getByTestId("keys-import-text").fill(MT6);
    await page.getByTestId("keys-import-check").click();
    await expect(page.getByTestId("keys-import-result")).toHaveAttribute("data-ok", "1");
    await page.getByTestId("keys-import-apply").click();
    await expect(page.getByTestId("keys-message")).toContainText("35 Antworten übernommen");
    await expect(page.getByTestId("keys-summary")).toContainText("35 Antworten");
    await expect(page.getByTestId("keys-summary")).toHaveAttribute("data-complete", "1");

    const answerOf = (n: number) => page.locator(`[data-testid="key-row"][data-number="${n}"]`).getByTestId("key-input");
    for (const [n, v] of [[1, "a"], [5, "e"], [16, "i"], [17, "j"], [21, "b"], [35, "b"]] as const) await expect(answerOf(n)).toHaveValue(v);
    await expect(answerOf(1)).toBeEnabled(); // Teil 1 (order A–E) is editable now

    // Teil 4: c = "Der Text sagt nichts dazu" is a valid answer (Hören true / false stays a / b / r / f)
    await answerOf(26).fill("c");
    await page.getByTestId("keys-save").click();
    await expect(page.getByTestId("keys-message")).toContainText("1 Antwort(en) gespeichert");
    const stored = await call("GET", `/admin/multilevel-exam/model-tests/${mt6}/answer-keys?section=LESEN`, admin);
    expect([stored.json.items[25].answer, stored.json.items[25].option_text.toLowerCase().slice(0, 13)]).toEqual(["c", "der text sagt"]);
    await answerOf(26).fill("b");
    await page.getByTestId("keys-save").click();
    await expect(page.getByTestId("keys-message")).toContainText("1 Antwort(en) gespeichert");
    const back = await call("GET", `/admin/multilevel-exam/model-tests/${mt6}/answer-keys?section=LESEN`, admin);
    expect(back.json.items.map((i: { answer: string }) => i.answer).join("")).toBe(LETTERS.join(""));
  });

  test("student: the Lesen sheet of Modelltest 6 is scored against its own key; the paper carries no key", async () => {
    const email = await createStudent();
    await grantMultilevelPremium(email);
    const student = await apiToken(email, PASSWORD);
    const attempt = await call("POST", "/multilevel-exam/attempts", student, { model_test_id: mt6 });
    expect(attempt.status, attempt.text).toBe(200);
    const id = attempt.json.attempt_id;
    const paper = await call("POST", `/multilevel-exam/attempts/${id}/sections/LESEN/start`, student);
    expect(paper.status, paper.text).toBe(200);
    expect(paper.text).not.toContain("is_correct"); // keys never reach a student before grading
    const questions = (paper.json.teile as { questions: { id: string; options: { id: string }[] }[] }[]).flatMap((t) => t.questions);
    expect(questions).toHaveLength(35);
    for (const [i, q] of questions.entries()) {
      const wrong = i >= 30; // the last five answered wrongly on purpose
      const index = LETTERS[i].charCodeAt(0) - 97;
      const pick = wrong ? q.options.findIndex((_o, j) => j !== index) : index;
      expect((await call("PUT", `/multilevel-exam/attempts/${id}/sections/LESEN/answers`, student, { question_id: q.id, option_ids: [q.options[pick].id] })).status).toBe(200);
    }
    expect((await call("POST", `/multilevel-exam/attempts/${id}/sections/LESEN/submit`, student)).status).toBe(200);
    expect((await call("POST", `/multilevel-exam/attempts/${id}/finish`, student)).status).toBe(200);
    const result = await call("GET", `/multilevel-exam/attempts/${id}/results`, student);
    const lesen = result.json.sections.find((s: { type: string }) => s.type === "LESEN");
    expect([lesen.raw_points, lesen.raw_max, lesen.no_key]).toEqual([30, 35, false]);
    expect(lesen.review.filter((r: { is_correct: boolean }) => r.is_correct)).toHaveLength(30);
  });
});
