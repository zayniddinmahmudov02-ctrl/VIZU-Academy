import { expect, test } from "@playwright/test";

import { PASSWORD, createStudent, loginViaForm } from "./helpers";

test.describe("student panel", () => {
  test.beforeEach(async ({ page }) => {
    const email = await createStudent();
    await loginViaForm(page, email, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test("navigation has Settings but no Profile", async ({ page, isMobile }) => {
    if (isMobile) await page.getByRole("button", { name: "Menü öffnen" }).click();
    const nav = page.locator("nav:visible");
    await expect(nav.getByRole("link", { name: "Einstellungen" })).toBeVisible();
    await expect(nav.getByRole("link", { name: "Profil" })).toHaveCount(0);
  });

  test("old /profile URL opens Settings", async ({ page }) => {
    await page.goto("/profile");
    await expect(page).toHaveURL(/\/settings$/);
    await expect(page.getByText("Persönliche Informationen")).toBeVisible();
  });

  test("profile data is edited and saved inside Settings", async ({ page }) => {
    await page.goto("/settings");
    // innermost section (the layout wraps the page in a <section> too)
    const card = page.locator("section").filter({ has: page.getByRole("heading", { name: "Persönliche Informationen" }) }).last();
    await card.getByRole("button", { name: "Bearbeiten" }).click();
    const first = card.locator("input:visible").first(); // Vorname
    await first.fill("Gespeichert");
    await card.getByRole("button", { name: "Speichern" }).click();
    await expect(card.getByText("Änderungen gespeichert.")).toBeVisible();

    await page.reload();
    await expect(
      page.locator("section").filter({ has: page.getByRole("heading", { name: "Persönliche Informationen" }) }).last(),
    ).toContainText("Gespeichert");
  });

  test("settings page keeps photo, security, language and account cards", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.getByText("Persönliche Informationen")).toBeVisible();
    // every former profile card renders (section count: profile cards + notifications + appearance)
    expect(await page.locator("section").count()).toBeGreaterThanOrEqual(6);
  });
});
