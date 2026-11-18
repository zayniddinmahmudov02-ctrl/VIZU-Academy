import { expect, test, type Page } from "@playwright/test";

import { ADMIN, PASSWORD, createStudent, loginViaForm } from "./helpers";

// Purchase page ("Xarid qilish"), packages, A1–C1 warning, promo code that needs an admin's approval, four interface
// languages, admin packages + payments tabs. Local stack only; promo E2EAPPROVE comes from D:\vz_tmp\work\purchase_e2e_seed.py.

async function noHorizontalScroll(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
}

// the login form is German (helpers.loginViaForm): switch the interface language only after signing in
async function setLang(page: Page, lang: "uz" | "de" | "en" | "ru") {
  await page.evaluate((l) => localStorage.setItem("vizu-language", JSON.stringify({ state: { language: l }, version: 0 })), lang);
  await page.reload();
}

async function adminLogin(page: Page) {
  await loginViaForm(page, ADMIN.email, ADMIN.password);
  await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
  await page.getByRole("button", { name: "Bestätigen" }).click();
  await expect(page).toHaveURL(/\/admin/);
}

test.describe.serial("purchase", () => {
  let student = "";

  test("packages, coming soon and the A1–C1 warning (uz)", async ({ page }, info) => {
    student = await createStudent();
    await loginViaForm(page, student, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);
    await setLang(page, "uz");
    await page.goto("/angebote");
    await expect(page.getByRole("heading", { name: "Xarid qilish" })).toBeVisible();

    for (const code of ["B2", "C1", "B2_C1"]) {
      const card = page.locator(`[data-offer="${code}"]`);
      await expect(card.getByTestId("offer-coming-soon")).toContainText("Tez orada");
      await expect(card.getByTestId("offer-buy")).toHaveCount(0);
    }
    await expect(page.locator('[data-offer="B1"]')).toContainText("100.000");
    await expect(page.locator('[data-offer="B1"] [data-testid="offer-duration"]')).toContainText("2 oylik");
    await expect(page.locator('[data-offer="A1_B1"]')).toContainText("200.000");
    await expect(page.locator('[data-offer="A1_C1"]')).toContainText("400.000");
    await expect(page.locator('[data-offer="A1_C1"] [data-testid="offer-later-note"]')).toBeVisible();
    await noHorizontalScroll(page);
    await page.screenshot({ path: `test-results/purchase-${info.project.name}.png`, fullPage: true });

    // A1–C1: warning first, cancel closes it, confirm opens the checkout
    await page.locator('[data-offer="A1_C1"]').getByTestId("offer-buy").click();
    await expect(page.getByTestId("package-warning")).toContainText("B2 va C1 kurslari platformaga qo'shilishi bilan");
    await page.getByTestId("package-warning-cancel").click();
    await expect(page.getByTestId("package-warning")).toHaveCount(0);
    await page.locator('[data-offer="A1_C1"]').getByTestId("offer-buy").click();
    await page.getByTestId("package-warning-confirm").click();
    await expect(page.getByRole("dialog")).toContainText("A1 → C1");
    await expect(page.getByRole("dialog")).toContainText("400.000 UZS");
  });

  test("promo code that needs approval: request → pending", async ({ page, isMobile }) => {
    test.skip(isMobile, "approval flow runs once (desktop)");
    await loginViaForm(page, student, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);
    await setLang(page, "uz");
    await page.goto("/angebote");
    await page.locator('[data-offer="A1_B1"]').getByTestId("offer-buy").click();
    const dialog = page.getByRole("dialog");
    await dialog.getByLabel("Chegirma kodi (ixtiyoriy)").fill("E2EAPPROVE");
    await dialog.getByRole("button", { name: "Qo'llash" }).click();
    await expect(dialog.getByTestId("promo-status")).toContainText("admin tomonidan tasdiqlanishi kerak");
    await dialog.getByTestId("promo-request-approval").click();
    await expect(dialog.getByTestId("promo-status")).toContainText("ko'rib chiqilmoqda");
    await expect(dialog).toContainText("200.000 UZS"); // no discount while pending
  });

  test("admin: packages, payments tabs without Telegram, approve the request", async ({ page, isMobile }) => {
    test.skip(isMobile, "admin checks run on desktop");
    await adminLogin(page);
    await page.goto("/admin/angebote");
    await expect(page.getByTestId("package-row-B1")).toContainText("100.000 UZS");
    await expect(page.getByTestId("package-row-B1")).toContainText("60 Tage");
    await expect(page.getByTestId("package-row-B2_C1")).toContainText("Bald verfügbar");
    await page.getByTestId("package-edit-A1_C1").click();
    await expect(page.getByTestId("package-price")).toHaveValue("400000");
    await page.getByRole("button", { name: "Abbrechen" }).click();

    await page.goto("/admin/payments");
    await expect(page.getByRole("tab", { name: "Telegram" })).toHaveCount(0);
    // the eight sections of Admin -> Payments (2026-11-16)
    for (const tab of ["Overview", "Payment Requests", "Course Payments", "Multilevel Modelltest Payments", "Promo Codes", "Promo Requests",
      "Purchase History", "Payment Settings"]) {
      await expect(page.getByRole("tab", { name: tab, exact: true })).toBeVisible();
    }
    await expect(page.getByTestId("discount-stats-tab")).toBeVisible(); // the discount figures are part of the overview
    await page.getByRole("tab", { name: "Promo Requests", exact: true }).click();
    const row = page.locator("tr", { hasText: student }).first();
    await expect(row).toContainText("E2EAPPROVE");
    await row.getByTestId("promo-request-approve").click();
    await expect(page.locator("tr", { hasText: student })).toHaveCount(0); // gone from the pending list
    await page.screenshot({ path: "test-results/purchase-admin.png", fullPage: true });
  });

  test("approved promo: the server applies the discount", async ({ page, isMobile }) => {
    test.skip(isMobile, "approval flow runs once (desktop)");
    await loginViaForm(page, student, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);
    await setLang(page, "uz");
    await page.goto("/angebote");
    await page.locator('[data-offer="A1_B1"]').getByTestId("offer-buy").click();
    const dialog = page.getByRole("dialog");
    await dialog.getByLabel("Chegirma kodi (ixtiyoriy)").fill("E2EAPPROVE");
    await dialog.getByRole("button", { name: "Qo'llash" }).click();
    await expect(dialog.getByTestId("promo-status")).toContainText("Tasdiqlandi");
    await expect(dialog).toContainText("180.000 UZS");
  });

  test("four interface languages", async ({ page, isMobile }) => {
    test.skip(isMobile, "sidebar language control is on desktop");
    await loginViaForm(page, student, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);
    await setLang(page, "uz");
    const nav = page.locator("aside");
    await expect(nav.getByRole("link", { name: "Xarid qilish" })).toBeVisible();
    for (const [code, label] of [["en", "Purchase"], ["ru", "Покупка"], ["de", "Angebote"]] as const) {
      await nav.locator(`button[data-lang="${code}"]`).click();
      await expect(nav.getByRole("link", { name: label })).toBeVisible();
    }
    await nav.locator('button[data-lang="ru"]').click();
    await page.goto("/angebote");
    await expect(page.locator('[data-offer="B2"]')).toContainText("Скоро");
    await page.screenshot({ path: "test-results/purchase-ru.png", fullPage: true });
  });
});
