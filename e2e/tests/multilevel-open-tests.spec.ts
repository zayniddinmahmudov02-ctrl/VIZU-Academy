import { expect, test, type Page } from "@playwright/test";

import { ADMIN, API_URL, PASSWORD, apiToken, createStudent, loginViaForm } from "./helpers";

// Multilevel Modelltest 1–6 open for every student (2026-11-18), local stack only. Admin: a Modelltest of 1–6 without Lesen keys / Hören
// audio shows only warnings and "Veröffentlichen" works; Modelltest 7 keeps the full rule. Student without any Premium: 1–6 are open, a test
// without audio starts, the Hören Teile show "audio not available" and can be answered, the exam finishes, the Lesen part without keys is
// "not scored" and the total is out of 225. The chosen Modelltest (2–6, no audio, no Lesen keys) is put back to its old status afterwards.

async function api(method: string, path: string, bearer: string, body?: unknown) {
  const res = await fetch(`${API_URL}/api/v1${path}`, {
    method, headers: { Authorization: `Bearer ${bearer}`, ...(body ? { "Content-Type": "application/json" } : {}) }, body: body ? JSON.stringify(body) : undefined,
  });
  return { status: res.status, json: await res.json().catch(() => null) };
}

async function adminLogin(page: Page) {
  await loginViaForm(page, ADMIN.email, ADMIN.password);
  await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
  await page.getByRole("button", { name: "Bestätigen" }).click();
  await expect(page).toHaveURL(/\/admin/);
}

async function confirmDialog(page: Page, label: string) {
  await page.locator("div.fixed").getByRole("button", { name: label }).click();
}

test.describe.serial("Multilevel Modelltest 1–6 open", () => {
  test.skip(({ isMobile }) => isMobile, "desktop");
  let admin = "";
  let number = 0; // a Modelltest of 2–6 without any Hören audio and without Lesen keys (other specs may have given 2 an audio / keys)
  const ids: Record<string, { id: string; url: string; status: string }> = {};

  test.beforeAll(async () => {
    admin = await apiToken(ADMIN.email, ADMIN.password);
    const all = (await api("GET", "/mock-exam/model-tests", admin)).json as { id: string; level_id: string; status: string }[];
    const levels = (await api("GET", "/mock-exam/levels", admin)).json as { id: string; provider_id: string }[];
    const overview = (await api("GET", "/admin/multilevel-audio", admin)).json as { tests: { model_test_id: string; sort_order: number; slots: { status: string }[] }[] };
    const entry = (id: string) => {
      const mt = all.find((t) => t.id === id)!;
      const level = levels.find((l) => l.id === mt.level_id)!;
      return { id, url: `/admin/mock-exams/${level.provider_id}/${mt.level_id}/${id}`, status: mt.status };
    };
    for (const t of overview.tests.filter((x) => x.sort_order >= 2 && x.sort_order <= 6)) {
      if (t.slots.some((s) => s.status !== "missing")) continue;
      const lesen = (await api("GET", `/admin/multilevel-exam/model-tests/${t.model_test_id}/answer-keys?section=LESEN`, admin)).json as { keys_set: number };
      if (lesen.keys_set === 0) { number = t.sort_order; ids.open = entry(t.model_test_id); break; }
    }
    expect(number, "no Modelltest 2–6 without audio and Lesen keys in the local DB").toBeGreaterThan(0);
    ids.seven = entry(overview.tests.find((x) => x.sort_order === 7)!.model_test_id);
  });

  test.afterAll(async () => {
    // the local DB gets its old status back (DRAFT is always allowed)
    if (ids.open && ids.open.status !== "PUBLISHED") await api("PUT", `/mock-exam/model-tests/${ids.open.id}`, admin, { status: ids.open.status });
  });

  test("admin: a Modelltest of 1–6 without Lesen keys / Hören audio — warnings only, Veröffentlichen works; Modelltest 7 keeps the full rule", async ({ page }) => {
    if (ids.open.status === "PUBLISHED") await api("PUT", `/mock-exam/model-tests/${ids.open.id}`, admin, { status: "DRAFT" });
    await adminLogin(page);
    await page.goto(ids.open.url);
    const panel = page.getByTestId("model-test-review");
    await expect(panel).toBeVisible();
    await expect(panel.getByTestId("publish-warnings")).toContainText("Nur Warnungen — Veröffentlichen ist möglich");
    await expect(panel.getByTestId("publish-warnings")).toContainText("Fragen ohne Lösung");
    await panel.getByTestId("toggle-publish").click();
    await expect(panel).toContainText("Veröffentlicht");
    await expect(panel.getByTestId("toggle-publish")).toContainText("Verbergen");
    await page.screenshot({ path: "test-results/ml-open-admin.png" });
    const statusOf = async (id: string) => ((await api("GET", "/mock-exam/model-tests", admin)).json as { id: string; status: string }[]).find((t) => t.id === id)!.status;
    expect(await statusOf(ids.open.id)).toBe("PUBLISHED");

    await page.goto(ids.seven.url);
    const p7 = page.getByTestId("model-test-review");
    await expect(p7).toBeVisible();
    await p7.getByTestId("toggle-publish").click();
    await expect(p7).toContainText("MODEL_TEST_NOT_READY");
    expect(await statusOf(ids.seven.id)).toBe("DRAFT");
  });

  test("student without Premium: Modelltest 1–6 open; a test without audio starts, Hören works, Lesen without keys is not scored", async ({ page }) => {
    test.setTimeout(120_000);
    const student = await createStudent();
    await loginViaForm(page, student, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);
    await page.goto("/vorbereitung/multilevel");
    for (const n of [1, number]) {
      const card = page.getByTestId(`multilevel-exam-${n}`);
      await expect(card).toHaveAttribute("data-access", "OPEN");
      await expect(card.getByTestId("start-exam")).toBeVisible();
    }
    for (const n of [2, 3, 4, 5, 6]) await expect(page.getByTestId(`multilevel-exam-${n}`)).not.toHaveAttribute("data-access", "LOCKED");
    await expect(page.getByTestId("multilevel-exam-7")).toHaveAttribute("data-access", "LOCKED");
    const bearer = await apiToken(student, PASSWORD);
    expect(((await api("GET", "/vizu-pay/multilevel", bearer)).json).entitled).toBe(false); // no Premium involved

    await page.getByTestId(`multilevel-exam-${number}`).getByTestId("start-exam").click();
    await expect(page.getByTestId("exam-overview")).toBeVisible();
    // Lesen: answer the first question, hand in
    await page.getByTestId("exam-section-LESEN").getByRole("button", { name: "Teil starten" }).click();
    await page.getByTestId("exam-question").first().getByTestId("exam-option").first().click();
    await expect(page.getByTestId("exam-question").first().getByText("Gespeichert")).toBeVisible();
    await page.getByTestId("submit-section").click();
    await confirmDialog(page, "Teil abgeben");
    await expect(page.getByTestId("exam-section-LESEN").getByText("Abgegeben")).toBeVisible({ timeout: 10_000 });
    // Hören without any audio: every Teil says so, the questions work
    await page.getByTestId("exam-section-HOEREN").getByRole("button", { name: "Teil starten" }).click();
    await expect(page.getByTestId("teil-audio-missing").first()).toBeVisible();
    expect(await page.getByTestId("teil-audio-missing").count()).toBe(await page.getByTestId("paper-teil").count());
    await page.getByTestId("exam-question").first().getByTestId("exam-option").first().click();
    await expect(page.getByTestId("exam-question").first().getByText("Gespeichert")).toBeVisible();
    await page.screenshot({ path: "test-results/ml-open-hoeren-no-audio.png" });
    await page.getByTestId("submit-section").click();
    await confirmDialog(page, "Teil abgeben");
    await expect(page.getByTestId("exam-section-HOEREN").getByText("Abgegeben")).toBeVisible({ timeout: 10_000 });
    await page.getByTestId("finish-exam").click();
    await confirmDialog(page, "Prüfung beenden");
    await expect(page).toHaveURL(/\/vorbereitung\/multilevel\/ergebnis\//);
    await expect(page.getByTestId("result-LESEN").getByTestId("section-no-key")).toBeVisible();
    await expect(page.getByTestId("result-HOEREN")).toContainText("/ 75");
    await expect(page.getByTestId("total-score")).toContainText("/ 225");
    await page.getByText(/Antworten ansehen — Lesen/).click();
    await expect(page.locator('[data-testid="review-item"][data-has-key="0"]').first()).toBeVisible();
    await page.screenshot({ path: "test-results/ml-open-result.png", fullPage: true });
  });
});

test("phone: Modelltest 1–6 open for a student without Premium, no horizontal scroll", async ({ page, isMobile }) => {
  test.skip(!isMobile, "phone");
  const student = await createStudent();
  await loginViaForm(page, student, PASSWORD);
  await expect(page).toHaveURL(/\/dashboard/);
  await page.goto("/vorbereitung/multilevel");
  await expect(page.getByTestId("multilevel-exam-1")).toHaveAttribute("data-access", "OPEN");
  await expect(page.getByTestId("multilevel-exam-7")).toHaveAttribute("data-access", "LOCKED");
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
});
