import { expect, test, type Page } from "@playwright/test";

import { ADMIN, API_URL, PASSWORD, createStudent, loginViaForm } from "./helpers";

// Free first lesson + purchase gating (A2: the local E2E database has 13 published A2 lessons). A student without a
// purchase opens lesson 1 ("Bepul"), every other lesson shows the purchase sheet and the API refuses it; after a real
// checkout + admin approval the whole level opens. Local stack only.

const GATE_TITLE = "Kursni davom ettirish uchun xarid qiling!";
const GATE_BODY = "Siz birinchi bepul darsni yakunladingiz.";

async function setLang(page: Page, lang: "uz" | "de") {
  await page.evaluate((l) => localStorage.setItem("vizu-language", JSON.stringify({ state: { language: l }, version: 0 })), lang);
  await page.reload();
}

async function token(email: string, password: string): Promise<string> {
  const res = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Forwarded-For": `10.88.${Math.floor(Math.random() * 250)}.${Math.floor(Math.random() * 250)}` },
    body: JSON.stringify({ identifier: email, password }),
  });
  expect(res.status, await res.clone().text()).toBe(200);
  return (await res.json()).access_token;
}

async function a2Lessons(bearer: string): Promise<{ id: string; number: number; free?: boolean; lock_reason: string | null }[]> {
  const res = await fetch(`${API_URL}/api/v1/lms/levels/A2`, { headers: { Authorization: `Bearer ${bearer}` } });
  expect(res.status).toBe(200);
  return (await res.json()).lessons;
}

async function lessonStatus(bearer: string, lessonId: string) {
  const res = await fetch(`${API_URL}/api/v1/lessons/${lessonId}`, { headers: { Authorization: `Bearer ${bearer}` } });
  return { status: res.status, body: await res.text() };
}

test.describe.serial("lesson gating", () => {
  let student = "";

  test("no purchase: lesson 1 free, lesson 2+ asks to buy (UI)", async ({ page }, info) => {
    student = await createStudent();
    await loginViaForm(page, student, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);
    await setLang(page, "uz");
    await page.goto("/kurse/a2");

    const cards = page.getByTestId("lms-lesson-card");
    await expect(cards.first()).toHaveAttribute("data-status", /not_started|in_progress|completed/);
    await expect(cards.first().getByTestId("lms-lesson-free")).toHaveText("Bepul");
    await expect(cards.nth(1)).toHaveAttribute("data-status", "locked");
    await expect(cards.nth(2)).toHaveAttribute("data-status", "locked");
    await expect(cards.nth(1).getByTestId("lms-lesson-free")).toHaveCount(0);

    // click on a closed lesson -> the purchase sheet at once
    await cards.nth(1).click();
    const sheet = page.getByTestId("lms-purchase-modal");
    await expect(sheet.getByTestId("lms-purchase-title")).toHaveText(GATE_TITLE);
    await expect(sheet.getByTestId("lms-purchase-text")).toContainText(GATE_BODY);
    await expect(sheet.getByTestId("lms-purchase-text")).toContainText("VIZU Academy bilan nemis tilini o‘rganishda davom eting!");
    await expect(sheet.getByTestId("lms-purchase-buy")).toHaveText(/Xarid qilish/);
    await expect(sheet.getByTestId("lms-purchase-back")).toHaveText(/Ortga qaytish/);
    await page.screenshot({ path: `test-results/gating-sheet-${info.project.name}.png`, fullPage: false });
    expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
    await sheet.getByTestId("lms-purchase-back").click();
    await expect(sheet).toHaveCount(0);
    await expect(page).toHaveURL(/\/kurse\/a2/);

    // lesson 1 opens; going on to lesson 2 directly shows the sheet, "Ortga qaytish" goes back
    await cards.first().getByTestId("lms-lesson-open").click();
    await expect(page).toHaveURL(/\/lektion\//);
    await expect(page.getByTestId("lms-lesson-lock")).toHaveCount(0);
    const bearer = await token(student, PASSWORD);
    const lessons = await a2Lessons(bearer);
    const firstUrl = page.url();
    await page.goto(`/lektion/${lessons[1].id}`);
    await expect(page.getByTestId("lms-purchase-title")).toHaveText(GATE_TITLE);
    await page.getByTestId("lms-purchase-back").click();
    await expect(page).toHaveURL(firstUrl);

    // "Xarid qilish" -> the purchase page
    await page.goto(`/lektion/${lessons[2].id}`);
    await page.getByTestId("lms-purchase-buy").click();
    await expect(page).toHaveURL(/\/angebote\?offer=A2/);
  });

  test("no purchase: the API refuses lesson 2+ and hides paid quizzes", async () => {
    const bearer = await token(student, PASSWORD);
    const lessons = await a2Lessons(bearer);
    expect(lessons[0].free).toBe(true);
    expect(lessons.slice(1).every((l) => l.free === false && l.lock_reason === "PREMIUM_REQUIRED")).toBe(true);
    expect((await lessonStatus(bearer, lessons[0].id)).status).toBe(200);
    for (const lesson of lessons.slice(1, 4)) {
      const r = await lessonStatus(bearer, lesson.id);
      expect(r.status).toBe(403);
      expect(r.body).toContain("PREMIUM_REQUIRED");
    }
    const hoeren = await fetch(`${API_URL}/api/v1/lesson-skills/${lessons[1].id}/hoeren`, { headers: { Authorization: `Bearer ${bearer}` } });
    expect(hoeren.status).toBe(403);
    // the old quiz lists answer only with what the caller may open (anonymous: nothing of a paid lesson)
    const anonymous = await fetch(`${API_URL}/api/v1/quiz-questions`);
    expect(anonymous.status).toBe(200);
  });

  test("purchase approved: the whole level opens", async ({ page, isMobile }) => {
    test.skip(isMobile, "purchase + approval run once (desktop)");
    await loginViaForm(page, student, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);
    await setLang(page, "uz");
    await page.goto("/angebote");
    await page.locator('[data-offer="A2"]').getByTestId("offer-buy").click();
    const dialog = page.getByRole("dialog");
    await dialog.locator('input[type="file"]').setInputFiles({ name: "chek.png", mimeType: "image/png",
      buffer: Buffer.from("89504e470d0a1a0a0000000d4948445200000001000000010806000000" + "1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082", "hex") });
    await dialog.getByRole("button", { name: "Buyurtmani yuborish" }).click();
    await expect(dialog).toHaveCount(0, { timeout: 15_000 });

    // still closed while the payment waits for approval
    let bearer = await token(student, PASSWORD);
    let lessons = await a2Lessons(bearer);
    expect((await lessonStatus(bearer, lessons[1].id)).status).toBe(403);

    const admin = await page.context().browser()!.newContext();
    const adminPage = await admin.newPage();
    await loginViaForm(adminPage, ADMIN.email, ADMIN.password);
    await adminPage.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
    await adminPage.getByRole("button", { name: "Bestätigen" }).click();
    await expect(adminPage).toHaveURL(/\/admin/);
    await adminPage.goto("/admin/payments");
    // Admin -> Payments opens on "Overview" since 2026-11-16; open requests are under "Payment Requests"
    await adminPage.getByRole("tab", { name: "Payment Requests", exact: true }).click();
    const card = adminPage.getByTestId("buyer-card").filter({ hasText: student });
    await card.getByRole("button", { name: "Genehmigen" }).click();
    await expect(card).toHaveCount(0, { timeout: 15_000 }); // approved: leaves the open requests (the API checks below prove it)
    await admin.close();

    bearer = await token(student, PASSWORD);
    lessons = await a2Lessons(bearer);
    expect(lessons.every((l) => l.lock_reason === null)).toBe(true);
    for (const lesson of lessons.slice(1, 4)) expect((await lessonStatus(bearer, lesson.id)).status).toBe(200);

    await page.goto("/kurse/a2");
    const cards = page.getByTestId("lms-lesson-card");
    await expect(cards.nth(1)).not.toHaveAttribute("data-status", "locked");
    await expect(page.getByTestId("lms-lesson-free")).toHaveCount(0); // owners see no "Bepul" badge
    await page.goto(`/lektion/${lessons[1].id}`);
    await expect(page.getByTestId("lms-lesson-lock")).toHaveCount(0);
    await expect(page.getByTestId("lms-purchase-modal")).toHaveCount(0);
  });
});
