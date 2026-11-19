import { expect, test, type Page } from "@playwright/test";

import { ADMIN, API_URL, PASSWORD, apiToken, createStudent, loginViaForm } from "./helpers";

// Multilevel Modelltest Premium (local stack only): all 10 Modelltests locked until the Premium, 99 000 so'm from the server, card
// payment with receipt / "Chek mavjud emas" + date and time, PENDING until the Super Admin approves (approve opens all 10, reject keeps
// them locked with the reason), admin note; promo codes start PENDING and work only after approval, a course code never works for the
// Multilevel Premium; "Promo so'rovi" for a course gets a personal code from the admin. Phone layout without horizontal scroll.

const PNG = Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), Buffer.alloc(64)]);

async function noHorizontalScroll(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(1);
}

async function api(method: string, path: string, bearer: string, body?: unknown) {
  const res = await fetch(`${API_URL}/api/v1${path}`, {
    method, headers: { Authorization: `Bearer ${bearer}`, ...(body ? { "Content-Type": "application/json" } : {}) }, body: body ? JSON.stringify(body) : undefined,
  });
  return { status: res.status, json: await res.json().catch(() => null) };
}

// the login form is German (helpers.loginViaForm); the student pages are checked in Uzbek — switched after the login, never with an
// init script (it would set the language again on every navigation, also for the next user in the same page)
async function setLang(page: Page, lang: "uz" | "de") {
  await page.evaluate((l) => localStorage.setItem("vizu-language", JSON.stringify({ state: { language: l }, version: 0 })), lang);
  await page.reload();
}

async function signOut(page: Page) {
  await page.context().clearCookies();
  await page.evaluate(() => localStorage.clear());
}

async function adminLogin(page: Page) {
  await loginViaForm(page, ADMIN.email, ADMIN.password);
  await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
  await page.getByRole("button", { name: "Bestätigen" }).click();
  await expect(page).toHaveURL(/\/admin/);
}

async function studentLogin(page: Page, email: string) {
  await loginViaForm(page, email, PASSWORD);
  await expect(page).toHaveURL(/\/dashboard/);
  await setLang(page, "uz");
}

async function studentOn(page: Page, email: string) {
  await studentLogin(page, email);
  await page.goto("/vorbereitung/multilevel");
  await expect(page.getByTestId("ml-premium-banner")).toBeVisible();
}

async function paymentsTab(page: Page, name: string) {
  await page.goto("/admin/payments");
  await page.getByRole("tab", { name, exact: true }).click();
}

test.describe.serial("multilevel modelltest premium", () => {
  test.skip(({ isMobile }) => isMobile, "the full flow runs once on desktop; the phone layout has its own test");
  let a = "";
  let b = "";
  let c = "";

  test.beforeAll(async () => {
    a = await createStudent();
    b = await createStudent();
    c = await createStudent();
  });

  test("student: all 10 Modelltests locked, the 99 000 so'm modal, card copy, receipt upload -> PENDING", async ({ page, context }) => {
    await context.grantPermissions(["clipboard-read", "clipboard-write"]);
    await studentOn(page, a);
    const cards = page.locator('[data-testid^="multilevel-exam-"]');
    await expect(cards).toHaveCount(10);
    for (let n = 1; n <= 10; n++) { // every Modelltest 1–10 needs the Premium (owner, 2026-11-19)
      const card = page.getByTestId(`multilevel-exam-${n}`);
      await expect(card.getByTestId("exam-description")).toHaveText("To'liq B1–C1 imtihon: Lesen, Hören, Schreiben, Sprechen."); // no import note
      await expect(card).toHaveAttribute("data-access", "LOCKED");
      await expect(card.getByTestId("exam-access")).toContainText("Yopiq");
      await expect(card.getByTestId("unlock-exam")).toBeVisible();
      await expect(card.getByTestId("start-exam")).toHaveCount(0);
    }
    await expect(page.getByTestId("ml-premium-banner")).toHaveAttribute("data-status", "LOCKED");
    await expect(page.getByTestId("ml-free-note")).toHaveCount(0); // nothing is free any more
    await expect(page.getByTestId("ml-premium-banner")).toContainText("10 ta Modelltest hali yopiq");
    // the server agrees
    const bearer = await apiToken(a, PASSWORD);
    const exams = (await api("GET", "/multilevel-exam/exams", bearer)).json as { model_test_id: string; number: number; is_locked: boolean }[];
    expect(exams.filter((e) => e.is_locked).map((e) => e.number)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
    const start1 = await api("POST", "/multilevel-exam/attempts", bearer, { model_test_id: exams.find((e) => e.number === 1)!.model_test_id });
    expect(start1.status).toBe(403); // Modelltest 1 too: PREMIUM_REQUIRED

    await page.getByTestId("multilevel-exam-8").getByTestId("unlock-exam").click();
    const modal = page.getByTestId("ml-premium-modal");
    await expect(modal).toBeVisible();
    await expect(modal).toContainText("VIZU MULTILEVEL MODELLTEST PREMIUM");
    await expect(modal.getByTestId("ml-price")).toHaveText("99 000 so‘m");
    for (const text of ["10 ta to'liq Modelltest", "Lesen, Hören, Schreiben, Sprechen", "Avtomatik natijalarni tekshirish", "Imtihon vaqtini nazorat qilish", "Natijalar tarixini saqlash"]) {
      await expect(modal.getByTestId("ml-features")).toContainText(text);
    }
    await expect(modal.getByTestId("ml-buy")).toHaveText("Sotib olish");
    await expect(modal.getByTestId("ml-enter-promo")).toHaveText("Promo Code kiritish");
    await modal.getByTestId("ml-buy").click();
    await expect(modal.getByTestId("ml-card-number")).toHaveText("9860 0401 1406 3742");
    await modal.getByTestId("ml-card-copy").click();
    await expect(modal.getByTestId("ml-card-copy")).toContainText("Nusxalandi");
    expect(await page.evaluate(() => navigator.clipboard.readText())).toBe("9860040114063742");
    await expect(modal.getByTestId("ml-amount")).toHaveValue("99 000 so‘m");
    await expect(modal.getByTestId("ml-instruction")).toContainText("99 000 so‘mni yuqoridagi karta raqamiga o'tkazing");
    // no receipt and no "Chek mavjud emas": refused in the form
    await modal.getByTestId("ml-submit").click();
    await expect(modal.getByTestId("ml-error")).toContainText("Chekni yuklang");
    await modal.getByTestId("ml-receipt").setInputFiles({ name: "chek.png", mimeType: "image/png", buffer: PNG });
    await modal.getByTestId("ml-note").fill("E2E: Kapitalbank orqali");
    await page.screenshot({ path: "test-results/ml-premium-pay.png" });
    await modal.getByTestId("ml-submit").click();
    await expect(modal.getByTestId("ml-sent")).toContainText("PENDING — Admin tasdig'ini kutmoqda.");
    await modal.getByRole("button", { name: "Yopish" }).last().click();
    await expect(page.getByTestId("ml-premium-banner")).toHaveAttribute("data-status", "PENDING");
    await expect(page.getByTestId("ml-status-pending")).toBeVisible();
    await expect(page.getByTestId("multilevel-exam-7")).toHaveAttribute("data-access", "LOCKED"); // pending opens nothing
    await noHorizontalScroll(page);
  });

  test("student without a receipt: date and time are required", async ({ page }) => {
    await studentOn(page, b);
    await page.getByTestId("ml-open-buy").click();
    const modal = page.getByTestId("ml-premium-modal");
    await modal.getByTestId("ml-buy").click();
    await modal.getByTestId("ml-no-receipt").check();
    await expect(modal.getByTestId("ml-receipt")).toHaveCount(0);
    await modal.getByTestId("ml-submit").click();
    await expect(modal.getByTestId("ml-error")).toContainText("To'lov sanasi va vaqtini kiriting");
    const now = new Date(Date.now() - 60 * 60 * 1000);
    const pad = (v: number) => String(v).padStart(2, "0");
    await modal.getByTestId("ml-paid-date").fill(`${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`);
    await modal.getByTestId("ml-paid-time").fill(`${pad(now.getHours())}:${pad(now.getMinutes())}`);
    await modal.getByTestId("ml-submit").click();
    await expect(modal.getByTestId("ml-sent")).toBeVisible();
  });

  test("admin: Multilevel payments — note, approve A (all 10 open), reject B with a reason", async ({ page }) => {
    await adminLogin(page);
    await paymentsTab(page, "Multilevel Modelltest Payments");
    const tab = page.getByTestId("multilevel-payments-tab");
    const cardA = tab.getByTestId("buyer-card").filter({ hasText: a });
    const cardB = tab.getByTestId("buyer-card").filter({ hasText: b });
    await expect(cardA).toBeVisible();
    await expect(cardA.getByTestId("buyer-category")).toHaveText("Multilevel Modelltest Premium");
    await expect(cardA.getByTestId("buyer-amount")).toContainText("99");
    await expect(cardA.getByTestId("buyer-student-note")).toContainText("Kapitalbank");
    await expect(cardA.getByRole("button", { name: "Beleg öffnen" })).toBeVisible();
    await expect(cardB.getByTestId("buyer-no-receipt")).toBeVisible();
    await expect(cardB.getByTestId("buyer-paid-at")).toBeVisible();
    await cardA.getByTestId("buyer-note-toggle").click();
    await cardA.getByTestId("buyer-note-input").fill("Chek tekshirildi (E2E)");
    await cardA.getByTestId("buyer-note-save").click();
    await expect(cardA.getByTestId("buyer-admin-note")).toContainText("Chek tekshirildi");
    await page.screenshot({ path: "test-results/ml-premium-admin.png", fullPage: true });
    await cardA.getByRole("button", { name: "Genehmigen" }).click();
    await expect(cardA).toHaveCount(0); // left the pending list
    await cardB.getByRole("button", { name: "Ablehnen" }).click();
    const dialog = page.getByRole("dialog");
    await dialog.getByRole("combobox").selectOption("Zahlung konnte nicht verifiziert werden");
    await dialog.getByRole("button", { name: "Ablehnen" }).click();
    await expect(cardB).toHaveCount(0);
    await expect(tab.getByTestId("ml-entitlements")).toContainText(a);
    await paymentsTab(page, "Overview");
    await expect(page.getByTestId("payments-overview")).toBeVisible();
    expect(Number(await page.getByTestId("ov-ml").locator("p").nth(1).innerText())).toBeGreaterThanOrEqual(1);
    expect(Number(await page.getByTestId("ov-ml-active").locator("p").nth(1).innerText())).toBeGreaterThanOrEqual(1);
    await paymentsTab(page, "Purchase History");
    await page.getByTestId("history-kind").selectOption("multilevel");
    await expect(page.getByTestId("payment-history-tab")).toContainText(a);
  });

  test("student A: Premium active, no Modelltest locked; student B: rejected with the reason, may send again", async ({ page }) => {
    await studentOn(page, a);
    await expect(page.getByTestId("ml-premium-banner")).toHaveAttribute("data-status", "ACTIVE");
    await expect(page.getByTestId("ml-status-active")).toContainText("Premium faol");
    for (let n = 1; n <= 10; n++) await expect(page.getByTestId(`multilevel-exam-${n}`)).not.toHaveAttribute("data-access", "LOCKED");
    await expect(page.locator('[data-access="LOCKED"]')).toHaveCount(0);
    await signOut(page);
    await studentOn(page, b);
    await expect(page.getByTestId("ml-status-rejected")).toContainText("Zahlung konnte nicht verifiziert werden");
    await expect(page.getByTestId("ml-open-buy")).toContainText("Qayta to'lov so'rovi yuborish");
    for (const n of [1, 7]) await expect(page.getByTestId(`multilevel-exam-${n}`)).toHaveAttribute("data-access", "LOCKED");
  });

  test("promo: a new Multilevel code is PENDING and does nothing; after the approval it opens everything; a course code never does", async ({ page }) => {
    const code = `E2EMLUI${Date.now().toString(36).toUpperCase()}`;
    await adminLogin(page);
    await paymentsTab(page, "Promo Codes");
    await page.getByRole("button", { name: "Yangi promokod" }).click();
    await page.locator("#promo-code").fill(code);
    await page.getByTestId("promo-category-select").selectOption("MULTILEVEL");
    await page.locator("#promo-type").selectOption("FREE_ACCESS");
    await expect(page.getByTestId("promo-multilevel-scope")).toContainText("Modelltest 1–10");
    await page.getByRole("button", { name: "Promokod yaratish" }).click();
    const row = page.locator("tr", { hasText: code });
    await expect(row.getByTestId("promo-status")).toHaveAttribute("data-status", "PENDING");
    await expect(row.getByTestId("promo-category")).toHaveAttribute("data-category", "MULTILEVEL");

    // student C: the PENDING code is refused
    const student = await apiToken(c, PASSWORD);
    expect((await api("GET", `/vizu-pay/multilevel/quote?promo_code=${code}`, student)).json.promo_error).toBe("PROMO_NOT_ACTIVE");
    expect((await api("POST", "/vizu-pay/multilevel/redeem", student, { code })).status).toBe(422);

    await row.getByTestId("promo-approve").click();
    await expect(row.getByTestId("promo-status")).toHaveAttribute("data-status", "ACTIVE");

    // a course (package) code, approved: never for the Multilevel Premium
    const admin = await apiToken(ADMIN.email, ADMIN.password);
    const courseCode = `E2ECRS${Date.now().toString(36).toUpperCase()}`;
    const created = await api("POST", "/admin/vizu-pay/promo-codes", admin, { code: courseCode, discount_type: "PERCENT", discount_value: 10,
      applicable_course_ids: [], applicable_package_codes: ["A1_B1"], max_uses: 5, max_uses_per_user: 1, product_category: "PACKAGES" });
    expect(created.status).toBe(200);
    expect((await api("POST", `/admin/vizu-pay/promo-codes/${created.json.id}/review`, admin, { action: "approve_activate" })).status).toBe(200);

    await signOut(page);
    await studentOn(page, c);
    await page.getByTestId("ml-open-promo").click();
    const modal = page.getByTestId("ml-premium-modal");
    await modal.getByTestId("ml-promo-input").fill(courseCode);
    await modal.getByTestId("ml-promo-check").click();
    await expect(modal.getByTestId("ml-error")).toContainText("Multilevel Modelltest uchun emas");
    await modal.getByTestId("ml-promo-input").fill(code);
    await modal.getByTestId("ml-promo-check").click();
    await expect(modal.getByTestId("ml-promo-result")).toContainText("bepul ochadi");
    await modal.getByTestId("ml-promo-unlock").click();
    await expect(modal.getByTestId("ml-redeemed")).toContainText("barcha 10 ta Modelltest ochildi");
    await modal.getByRole("button", { name: "Yopish" }).last().click();
    await expect(page.getByTestId("ml-premium-banner")).toHaveAttribute("data-status", "ACTIVE");
    await expect(page.locator('[data-access="LOCKED"]')).toHaveCount(0);
    // and the Multilevel code is no course discount
    expect((await api("GET", `/vizu-pay/quote?plan=A1_B1&promo_code=${code}`, student)).json.promo_error).toBe("PROMO_WRONG_PRODUCT");
  });

  test("course promo request: student asks, admin creates a personal code, the student sees it (nothing is opened by it)", async ({ page }) => {
    await studentLogin(page, b);
    await page.goto("/angebote");
    const box = page.getByTestId("course-promo-request");
    await expect(box).toContainText("Promo so'rovi");
    await box.getByTestId("course-request-plan").selectOption("A1_B1");
    await box.getByTestId("course-request-message").fill("Talabaman, chegirma so'rayman");
    await box.getByTestId("course-request-send").click();
    await expect(box.getByTestId("course-request-sent")).toBeVisible();
    await expect(page.locator('[data-testid="promo-request-row"][data-kind="COURSE_REQUEST"]').first()).toHaveAttribute("data-status", "PENDING_APPROVAL");
    await noHorizontalScroll(page);

    await signOut(page);
    await adminLogin(page);
    await paymentsTab(page, "Promo Requests");
    await page.getByTestId("promo-requests-kind").selectOption("COURSE_REQUEST");
    const row = page.locator("tr", { hasText: b }).first();
    await expect(row.getByTestId("promo-request-message")).toContainText("Talabaman");
    await row.getByTestId("promo-request-approve").click();
    const dialog = page.getByTestId("course-review-dialog");
    await dialog.getByTestId("course-review-type").selectOption("PERCENT");
    await dialog.getByTestId("course-review-value").fill("50");
    await page.getByTestId("course-review-submit").click();
    await expect(page.locator("tr", { hasText: b })).toHaveCount(0); // left the pending list

    await signOut(page);
    await studentLogin(page, b);
    await page.goto("/angebote");
    const approved = page.locator('[data-testid="promo-request-row"][data-kind="COURSE_REQUEST"][data-status="APPROVED"]').first();
    await expect(approved.getByTestId("promo-request-code")).toContainText("REQ-");
    await expect(approved.getByTestId("promo-request-code")).toContainText("50% chegirma");
    // the approval bought nothing
    const bearer = await apiToken(b, PASSWORD);
    expect(((await api("GET", "/vizu-pay/status", bearer)).json.owned_levels as string[]).length).toBe(0);
  });
});

test("phone: locked cards, premium modal and payment form fit the screen", async ({ page, isMobile }) => {
  test.skip(!isMobile, "phone layout");
  const email = await createStudent();
  await studentOn(page, email);
  await expect(page.locator('[data-testid^="multilevel-exam-"]')).toHaveCount(10);
  await noHorizontalScroll(page);
  await page.getByTestId("ml-open-buy").click();
  const modal = page.getByTestId("ml-premium-modal");
  await expect(modal.getByTestId("ml-price")).toHaveText("99 000 so‘m");
  await modal.getByTestId("ml-buy").click();
  await expect(modal.getByTestId("ml-card-number")).toBeVisible();
  const box = await modal.boundingBox();
  const viewport = page.viewportSize()!;
  expect(box!.x).toBeGreaterThanOrEqual(0);
  expect(box!.x + box!.width).toBeLessThanOrEqual(viewport.width + 1);
  await modal.getByTestId("ml-no-receipt").check();
  await expect(modal.getByTestId("ml-paid-date")).toBeVisible();
  await page.screenshot({ path: "test-results/ml-premium-phone.png" });
  await noHorizontalScroll(page);
});
