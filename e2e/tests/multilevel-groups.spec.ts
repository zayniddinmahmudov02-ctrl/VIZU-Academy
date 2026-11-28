import { expect, test, type Page } from "@playwright/test";

import { ADMIN, PASSWORD, loginViaForm } from "./helpers";

// Multilevel groups (owner 2026-11-28): a group linked to "Multilevel B1–C1" opens the Modelltests for its members without the Premium and
// shows the teacher every member's results (read only). Needs the seed D:\vz_tmp\work\mlg_e2e_seed.py on vizu_gcr_e2e (teacher, s1 with two
// graded attempts 180 / 268, s2 without, an outsider). Local stack only.

const TEACHER = "mlg-teacher@example.com";
const S1 = "mlg-s1@example.com";
const OUT = "mlg-out@example.com";
const GROUP = "Multilevel E2E 1.Gruppe";

async function uz(page: Page) {
  await page.evaluate(() => localStorage.setItem("vizu-language", JSON.stringify({ state: { language: "uz" }, version: 0 })));
}

function noHorizontalScroll(page: Page) {
  return page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
}

test.describe("Multilevel groups", () => {
  test("member: Modelltests open through the group, own results in the group", async ({ page }, info) => {
    await loginViaForm(page, S1, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);
    await uz(page);
    await page.goto("/vorbereitung/multilevel");
    await expect(page.getByTestId("ml-premium-banner")).toHaveAttribute("data-status", "GROUP");
    await expect(page.getByTestId("ml-status-group")).toContainText(GROUP);
    await expect(page.locator('[data-access="OPEN"]').first()).toBeVisible();
    await expect(page.getByTestId("ml-open-buy")).toHaveCount(0);

    await page.goto("/groups");
    await page.getByText(GROUP).first().click();
    await expect(page.getByRole("tab", { name: "Multilevel" })).toHaveAttribute("aria-selected", "true"); // opens on the Multilevel tab
    const mine = page.getByTestId("ml-mine");
    await expect(mine.getByTestId("ml-attempt")).toHaveCount(2);
    await expect(mine.getByTestId("ml-attempt-total").first()).toHaveText("268 / 300");
    await expect(mine.getByTestId("ml-go-tests")).toHaveAttribute("href", "/vorbereitung/multilevel");
    expect(await noHorizontalScroll(page)).toBeLessThanOrEqual(1);
    await page.screenshot({ path: `test-results/ml-group-student-${info.project.name}.png`, fullPage: true });
  });

  test("outsider: still locked", async ({ page }) => {
    await loginViaForm(page, OUT, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);
    await page.goto("/vorbereitung/multilevel");
    await expect(page.getByTestId("ml-premium-banner")).toHaveAttribute("data-status", "LOCKED");
    await expect(page.locator('[data-access="OPEN"]')).toHaveCount(0);
  });

  test("teacher: results of every member, drill-down per Modelltest, read only", async ({ page }, info) => {
    await loginViaForm(page, TEACHER, PASSWORD);
    await expect(page).toHaveURL(/\/teacher/);
    await uz(page);
    await page.goto("/teacher/groups");
    await page.getByText(GROUP).first().click();
    await expect(page.getByTestId("group-ml-badge")).toContainText("Multilevel B1–C1");
    const table = page.getByTestId("ml-students-table");
    await expect(table.getByTestId("ml-student-row")).toHaveCount(2);
    const s1 = table.getByTestId("ml-student-row").filter({ hasText: "Aziz" });
    await expect(s1.getByTestId("ml-total")).toHaveText("268 / 300");
    await expect(s1.getByTestId("ml-tests-taken")).toHaveText(/^1 \/ \d+$/);
    await expect(s1.getByTestId("ml-attempts")).toHaveText("2");
    await expect(s1.getByTestId("ml-level")).toContainText("C1");
    const s2 = table.getByTestId("ml-student-row").filter({ hasText: "Malika" });
    await expect(s2.getByTestId("ml-total")).toHaveText("—");
    await page.screenshot({ path: `test-results/ml-group-teacher-${info.project.name}.png`, fullPage: true });

    await s1.click();
    const detail = page.getByTestId("ml-student-detail");
    await expect(detail.getByTestId("ml-attempt")).toHaveCount(2);
    await expect(detail.getByTestId("ml-attempt-total")).toHaveText(["268 / 300", "180 / 300"]);
    await expect(detail.getByTestId("ml-sec-SCHREIBEN").first()).toContainText("65");
    await expect(detail.locator("input, textarea, select")).toHaveCount(0); // read only: nothing to edit
    expect(await noHorizontalScroll(page)).toBeLessThanOrEqual(1);

    // the teacher cannot link / unlink: the settings form has no Multilevel select
    await page.getByRole("tab", { name: /Sozlamalar|Einstellungen/ }).click();
    await expect(page.getByTestId("group-form")).toBeVisible();
    await expect(page.getByTestId("group-multilevel")).toHaveCount(0);
  });

  test("super admin: the Multilevel link in the group form", async ({ page, isMobile }) => {
    test.skip(isMobile, "admin check runs on desktop");
    await loginViaForm(page, ADMIN.email, ADMIN.password);
    await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
    await page.getByRole("button", { name: "Bestätigen" }).click();
    await expect(page).toHaveURL(/\/admin/);
    await page.goto("/admin/groups");
    await page.getByText(GROUP).first().click();
    await page.getByRole("tab", { name: /Einstellungen|Sozlamalar/ }).click();
    const select = page.getByTestId("group-multilevel");
    await expect(select).toBeVisible();
    await expect(select.locator("option:checked")).toHaveText("Multilevel B1–C1");
  });
});
