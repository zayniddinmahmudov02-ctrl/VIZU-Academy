import { expect, test } from "@playwright/test";

import { ADMIN, loginViaForm } from "./helpers";

test.describe("admin panel", () => {
  test.skip(({ isMobile }) => isMobile, "admin checks run on desktop");

  test.beforeEach(async ({ page }) => {
    await loginViaForm(page, ADMIN.email, ADMIN.password);
    await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
    await page.getByRole("button", { name: "Bestätigen" }).click();
    await expect(page).toHaveURL(/\/admin/);
  });

  test("sidebar has Media Management and other sections but no A2 Audio", async ({ page }) => {
    const nav = page.locator("aside nav, nav").first();
    for (const label of ["Dashboard", "Werbung-Banner", "Media Management", "Vorbereitung", "VIZU-Multilevel", "Users", "Payments"]) {
      await expect(nav.getByRole("link", { name: label, exact: true })).toBeVisible();
    }
    await expect(page.getByRole("link", { name: /A2 Audio/i })).toHaveCount(0);
  });

  test("legacy A2 Audio URL lands in Media Management", async ({ page }) => {
    await page.goto("/admin/media-management/a2-audio");
    await expect(page).toHaveURL(/\/admin\/media-management\?level=A2$/);
  });
});
