import { execFileSync } from "node:child_process";

import { expect, test, type Page } from "@playwright/test";

import { ADMIN, API_URL, PASSWORD, createStudent, grantMultilevelPremium, loginViaForm, useLanguage } from "./helpers";

// Multilevel Modelltest 1–6: the Hören answer keys in the admin (numbered table, edit, import check), the exam times 60 / 60 / 60 / 15 = 195 and the server timer in the
// student exam. Local stack only: the Hören keys + exam times of the local e2e database were set before by
//   python -m app.scripts.multilevel_hoeren_keys apply --confirm <plan id> --overwrite
// and one part of the timer test moves a deadline with D:\vz_tmp\work\ml_expire.py (E2E_PYTHON / E2E_EXPIRE_SCRIPT override the paths).
const PYTHON = process.env.E2E_PYTHON ?? "D:\\vz_tmp\\venv\\Scripts\\python.exe";
const EXPIRE = process.env.E2E_EXPIRE_SCRIPT ?? "D:\\vz_tmp\\work\\ml_expire.py";
const COUNTS: Record<number, number> = { 1: 35, 2: 30, 3: 30, 4: 30, 5: 30, 6: 30 };
const MT2 = "1-r, 2-a, 3-f, 4-b, 5-r\n6-c, 7-f, 8-c, 9-f, 10-c\n11-b, 12-a, 13-c, 14-a, 15-b\n16-b, 17-c, 18-a, 19-b, 20-c\n21-c, 22-c, 23-c, 24-a, 25-b\n26-b, 27-a, 28-c, 29-b, 30-a";

async function token(email: string, password: string) {
  const res = await fetch(`${API_URL}/api/v1/auth/login`, { method: "POST", headers: { "Content-Type": "application/json", "X-Forwarded-For": `10.94.${Math.floor(Math.random() * 250)}.${Math.floor(Math.random() * 250)}` }, body: JSON.stringify({ identifier: email, password }) });
  expect(res.status, await res.clone().text()).toBe(200);
  return (await res.json()).access_token as string;
}
const call = async (method: string, url: string, bearer: string | null, body?: unknown) => {
  const res = await fetch(`${API_URL}/api/v1${url}`, { method, headers: { ...(bearer ? { Authorization: `Bearer ${bearer}` } : {}), ...(body ? { "Content-Type": "application/json" } : {}) }, body: body ? JSON.stringify(body) : undefined });
  const text = await res.text();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return { status: res.status, json: (text && res.headers.get("content-type")?.includes("json") ? JSON.parse(text) : null) as any };
};
async function noHorizontalScroll(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
}
async function adminLogin(page: Page) {
  await page.addInitScript(() => localStorage.setItem("vizu-language", JSON.stringify({ state: { language: "de" }, version: 0 })));
  await loginViaForm(page, ADMIN.email, ADMIN.password);
  await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
  await page.getByRole("button", { name: "Bestätigen" }).click();
  await expect(page).toHaveURL(/\/admin/);
}

test.describe.serial("Multilevel Modelltest: Hören answer keys and exam times", () => {
  let admin = "";

  test.beforeAll(async () => {
    admin = await token(ADMIN.email, ADMIN.password);
  });

  test("security: the answer-key routes are closed to anonymous users and students", async () => {
    const student = await createStudent();
    const bearer = await token(student, PASSWORD);
    const base = "/admin/multilevel-exam/model-tests/00000000-0000-0000-0000-000000000000/answer-keys";
    expect((await call("GET", base, null)).status).toBe(401);
    expect((await call("PUT", base, null, { section: "HOEREN", answers: { "1": "b" } })).status).toBe(401);
    expect((await call("POST", `${base}/import`, null, { section: "HOEREN", text: "1-b" })).status).toBe(401);
    for (const [method, url, body] of [["GET", base, undefined], ["PUT", base, { section: "HOEREN", answers: { "1": "b" } }], ["POST", `${base}/import`, { section: "HOEREN", text: "1-b" }]] as const) {
      expect((await call(method, url, bearer, body)).status, `${method} ${url}`).toBe(403);
    }
    expect((await call("GET", base, admin)).status).toBe(404); // an admin may read, an unknown test does not exist
  });

  test("admin: six Hören answer keys with 35 / 30 questions, edit, validation, import check", async ({ page }) => {
    await adminLogin(page);
    await page.goto("/admin/mock-exams/multilevel");
    const card = page.getByTestId("keys-card");
    await expect(card).toBeVisible({ timeout: 30_000 });
    const select = page.getByTestId("keys-test");
    const options = await select.locator("option").allTextContents();
    expect(options.slice(0, 6).map((o) => o.split(" · ")[0])).toEqual(["Modelltest 1", "Modelltest 2", "Modelltest 3", "Modelltest 4", "Modelltest 5", "Modelltest 6"]);
    // every test has its own numbered table of the right size, complete, in the owner's letters
    for (const [number, count] of Object.entries(COUNTS)) {
      await select.selectOption({ label: options[Number(number) - 1] });
      await expect(page.getByTestId("keys-summary")).toContainText(`Modelltest ${number} · Hören`);
      await expect(page.getByTestId("keys-summary")).toContainText(`${count} Fragen`);
      await expect(page.getByTestId("keys-summary")).toContainText(`${count} Antworten`);
      await expect(page.getByTestId("keys-summary")).toHaveAttribute("data-complete", "1");
      await expect(page.getByTestId("key-row")).toHaveCount(count);
    }
    const answerOf = (n: number) => page.locator(`[data-testid="key-row"][data-number="${n}"]`).getByTestId("key-input");
    await select.selectOption({ label: options[0] });
    await expect(answerOf(1)).toHaveValue("b");
    await expect(answerOf(16)).toHaveValue("h"); // matching A–H: the 8th option
    await expect(answerOf(35)).toHaveValue("b");
    await select.selectOption({ label: options[2] });
    await expect(answerOf(1)).toHaveValue("F"); // upper case stays upper case
    await expect(answerOf(3)).toHaveValue("R");
    await select.selectOption({ label: options[5] });
    await expect(answerOf(2)).toHaveValue("B");
    await select.selectOption({ label: options[1] });
    await expect(answerOf(1)).toHaveValue("r");

    // the publish check names what is still missing (Lesen keys and Hören audio of the owner)
    await expect(page.getByTestId("keys-readiness")).toHaveAttribute("data-ready", "0");

    // an invalid letter is refused before anything is sent; a valid change is saved and survives a reload
    await answerOf(2).fill("z");
    await expect(answerOf(2)).toHaveValue("z");
    await page.getByTestId("keys-save").click();
    await expect(page.getByTestId("keys-message")).toContainText("Ungültige Antwort bei Nr. 2");
    await answerOf(2).fill("c");
    await answerOf(3).fill("R");
    await page.getByTestId("keys-save").click();
    await expect(page.getByTestId("keys-message")).toContainText("2 Antwort(en) gespeichert");
    await page.reload();
    await page.getByTestId("keys-test").selectOption({ label: options[1] });
    await expect(answerOf(2)).toHaveValue("c");
    await expect(answerOf(3)).toHaveValue("R");
    const stored = await call("GET", `/admin/multilevel-exam/model-tests/${await modelTestId(page)}/answer-keys?section=HOEREN`, admin);
    expect(stored.json.items[2].answer).toBe("R"); // the token as typed
    expect(stored.json.items[2].option_text).toBe("Richtig");

    // import: a list with a wrong count is checked and cannot be applied; the full list restores the owner's keys
    await page.getByTestId("keys-import-text").fill(MT2.replace("30-a", ""));
    await page.getByTestId("keys-import-check").click();
    await expect(page.getByTestId("keys-import-result")).toHaveAttribute("data-ok", "0");
    await expect(page.getByTestId("keys-import-result")).toContainText("29 Antworten für 30 Fragen");
    await expect(page.getByTestId("keys-import-apply")).toBeDisabled();
    await page.getByTestId("keys-import-text").fill(`${MT2}\n31-a`);
    await page.getByTestId("keys-import-check").click();
    await expect(page.getByTestId("keys-import-result")).toContainText("Diese Frage gibt es nicht");
    await page.getByTestId("keys-import-text").fill(MT2);
    await page.getByTestId("keys-import-check").click();
    await expect(page.getByTestId("keys-import-result")).toHaveAttribute("data-ok", "1");
    await page.getByTestId("keys-import-apply").click();
    await expect(page.getByTestId("keys-message")).toContainText("30 Antworten übernommen");
    await expect(answerOf(2)).toHaveValue("a");
    await expect(answerOf(3)).toHaveValue("f");
  });

  test("exam times: Lesen 60, Hören 60, Schreiben 60, Sprechen 15 = 195 minutes in every Modelltest", async () => {
    const student = await createStudent();
    const bearer = await token(student, PASSWORD);
    const exams = (await call("GET", "/multilevel-exam/exams", bearer)).json as { number: number; total_minutes: number; sections: { type: string; duration_minutes: number }[] }[];
    expect(exams.length).toBeGreaterThan(0);
    for (const exam of exams) {
      expect(exam.sections.map((s) => [s.type, s.duration_minutes]), `Modelltest ${exam.number}`).toEqual([["LESEN", 60], ["HOEREN", 60], ["SCHREIBEN", 60], ["SPRECHEN", 15]]);
      expect(exam.total_minutes).toBe(195);
    }
  });

  test("student: Modelltest card, 195 minutes, server timer survives a reload and the section closes by itself at the deadline", async ({ page, isMobile }) => {
    test.setTimeout(120_000);
    await useLanguage(page, "de");
    const email = await createStudent();
    await grantMultilevelPremium(email); // every Multilevel Modelltest needs the Premium
    await loginViaForm(page, email, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);
    await page.goto("/vorbereitung/multilevel");
    const card = page.getByTestId("multilevel-exam-1");
    await expect(card).toBeVisible();
    await expect(card.getByTestId("exam-title")).toHaveText("Modelltest 1");
    await expect(card).toContainText("VIZU Multilevel");
    await expect(card.getByTestId("exam-state")).toHaveText("Neu");
    for (const [type, minutes] of [["LESEN", 60], ["HOEREN", 60], ["SCHREIBEN", 60], ["SPRECHEN", 15]] as const) {
      await expect(card.getByTestId(`exam-section-line-${type}`)).toContainText(`${minutes} Min.`);
    }
    await expect(card.getByTestId("exam-total")).toContainText("195 Min. (3 Std. 15 Min.)");
    await noHorizontalScroll(page);
    if (isMobile) await page.screenshot({ path: "test-results/multilevel-card-mobile.png" });
    await card.getByTestId("start-exam").click();
    await expect(page.getByTestId("exam-overview")).toBeVisible();
    await expect(page.getByTestId("exam-brand")).toHaveText("VIZU MULTILEVEL MODELLTEST 1");
    await expect(page.getByTestId("exam-total")).toContainText("195 Min.");
    for (const [type, minutes] of [["LESEN", 60], ["HOEREN", 60], ["SCHREIBEN", 60], ["SPRECHEN", 15]] as const) {
      await expect(page.getByTestId(`exam-section-${type}`)).toHaveAttribute("data-minutes", String(minutes));
    }
    await noHorizontalScroll(page);
    const attemptId = page.url().split("/").pop()!;
    const bearer = await token(email, PASSWORD);

    // Hören starts at 60:00 on the server
    await page.getByTestId("exam-section-HOEREN").getByRole("button", { name: "Teil starten" }).click();
    await expect(page.getByTestId("exam-section")).toBeVisible();
    await expect(page.getByTestId("exam-timer")).toHaveText(/^(60:00|59:5\d)$/, { timeout: 10_000 });
    const first = page.getByTestId("exam-question").first();
    await first.getByTestId("exam-option").nth(0).click();
    await expect(first.getByText("Gespeichert")).toBeVisible();
    await page.waitForTimeout(2500);
    const before = await page.getByTestId("exam-timer").innerText();
    // reload: the timer continues (it is not reset to 60:00)
    await page.reload();
    await page.getByTestId("exam-section-HOEREN").getByRole("button", { name: "Weiter" }).click();
    const afterText = await page.getByTestId("exam-timer").innerText();
    const secs = (s: string) => Number(s.split(":")[0]) * 60 + Number(s.split(":")[1]);
    expect(secs(afterText)).toBeLessThanOrEqual(secs(before));
    expect(secs(afterText)).toBeGreaterThan(secs(before) - 30);
    expect(secs(afterText)).toBeLessThan(3600);
    const view = (await call("GET", `/multilevel-exam/attempts/${attemptId}`, bearer)).json;
    const hoeren = view.sections.find((s: { type: string }) => s.type === "HOEREN");
    expect(hoeren.duration_seconds).toBe(3600);
    expect(hoeren.remaining_seconds).toBeLessThan(3600);
    expect(hoeren.remaining_seconds).toBeGreaterThan(3500);
    await noHorizontalScroll(page);

    // the deadline is almost there (the server clock decides: the page takes the new remaining time when it is opened again), the timer reaches 0,
    // the page hands the section in itself, the server stores the result and refuses further answers
    execFileSync(PYTHON, [EXPIRE, attemptId, "HOEREN", "9"], { stdio: "pipe", env: process.env });
    await page.reload();
    await page.getByTestId("exam-section-HOEREN").getByRole("button", { name: "Weiter" }).click();
    await expect(page.getByTestId("exam-timer")).toHaveText(/^00:0\d$/);
    await expect(page.getByTestId("exam-timer")).toHaveAttribute("data-expired", "1", { timeout: 15_000 });
    await expect.poll(async () => (await call("GET", `/multilevel-exam/attempts/${attemptId}`, bearer)).json.sections.find((s: { type: string }) => s.type === "HOEREN").status, { timeout: 20_000 }).toMatch(/SUBMITTED|EXPIRED/);
    const closed = (await call("GET", `/multilevel-exam/attempts/${attemptId}`, bearer)).json.sections.find((s: { type: string }) => s.type === "HOEREN");
    expect(closed.ended_at).not.toBeNull();
    expect(closed.remaining_seconds).toBeNull();
    const paper = (await call("GET", `/multilevel-exam/attempts/${attemptId}/sections/HOEREN`, bearer));
    expect(paper.status).toBe(409); // the section is closed
    // Lesen is still untouched and has its own 60 minutes
    await expect(page.getByTestId("exam-section-HOEREN")).toContainText(/Abgegeben|Zeit abgelaufen/, { timeout: 15_000 });
    await expect(page.getByTestId("exam-section-LESEN")).toHaveAttribute("data-minutes", "60");
  });
});

async function modelTestId(page: Page): Promise<string> {
  // the select holds the ids as option values
  return page.getByTestId("keys-test").evaluate((el: HTMLSelectElement) => el.value);
}
