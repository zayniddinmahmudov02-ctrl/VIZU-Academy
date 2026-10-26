import { expect, test } from "@playwright/test";

import { API_URL, PASSWORD, createStudent, loginViaForm, useLanguage } from "./helpers";

test.describe("welcome page", () => {
  test("shows both choices and the first goes to Login", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Willkommen bei VIZU-DEUTSCH" })).toBeVisible();
    await expect(page.getByText("Lerne Deutsch mit unserem digitalen Lernsystem.")).toBeVisible();
    await page.getByRole("link", { name: /Ich habe bereits ein Konto/ }).click();
    await expect(page).toHaveURL(/\/login$/);
  });

  test("primary choice text is white on navy (readable)", async ({ page }) => {
    await page.goto("/");
    const title = page.getByText("Ich habe bereits ein Konto", { exact: true });
    await expect(title).toHaveCSS("color", "rgb(255, 255, 255)");
  });

  test("the second choice goes to Registration", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: /Ich bin neu hier/ }).click();
    await expect(page).toHaveURL(/\/register$/);
  });

  test("choices work with the keyboard", async ({ page }) => {
    await page.goto("/");
    const link = page.getByRole("link", { name: /Ich habe bereits ein Konto/ });
    await link.focus();
    await page.keyboard.press("Enter");
    await expect(page).toHaveURL(/\/login$/);
  });

  test("Uzbek texts", async ({ page }) => {
    await useLanguage(page, "uz");
    await page.goto("/");
    await expect(page.getByRole("link", { name: /Avvaldan akkauntingiz bormi\?/ })).toBeVisible();
    await expect(page.getByRole("link", { name: /Birinchi marta kiryapsizmi\?/ })).toBeVisible();
  });

  test("an active session skips the welcome page", async ({ page }) => {
    const email = await createStudent();
    await loginViaForm(page, email, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);
    await page.goto("/");
    await expect(page).toHaveURL(/\/dashboard/);
  });
});

test.describe("help dialog", () => {
  for (const [path, title] of [["/login", "So meldest du dich an"], ["/register", "So registrierst du dich"]] as const) {
    test(`${path}: opens, closes with Escape, keeps the form`, async ({ page }) => {
      await page.goto(path);
      const identifier = page.getByPlaceholder("E-Mail oder +998 90 123 45 67");
      await identifier.fill("keep@example.com");

      const trigger = page.getByRole("button", { name: "Hilfe" });
      await trigger.click();
      const dialog = page.getByRole("dialog", { name: title });
      await expect(dialog).toBeVisible();
      await expect(dialog.locator("li")).toHaveCount(6);
      await expect(dialog).toBeInViewport();

      await page.keyboard.press("Escape");
      await expect(dialog).toBeHidden();
      await expect(trigger).toBeFocused();
      await expect(identifier).toHaveValue("keep@example.com");
    });
  }

  test("close button and Uzbek text", async ({ page }) => {
    await useLanguage(page, "uz");
    await page.goto("/login");
    await page.getByRole("button", { name: "Yordam" }).click();
    const dialog = page.getByRole("dialog", { name: "Qanday qilib akkauntga kirasiz?" });
    await expect(dialog).toContainText("Kirish sahifasini oching.");
    await dialog.getByRole("button", { name: "Yopish" }).click();
    await expect(dialog).toBeHidden();
  });
});

test.describe("login", () => {
  test("wrong password is refused, identifier kept, password cleared of nothing secret", async ({ page }) => {
    const email = await createStudent();
    await loginViaForm(page, email, "falsch-123");
    await expect(page.getByText("E-Mail/Telefonnummer oder Passwort ist falsch.")).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByPlaceholder("E-Mail oder +998 90 123 45 67")).toHaveValue(email);
    await expect(page.locator("body")).not.toContainText("Traceback");
  });

  test("password is never written to browser storage", async ({ page }) => {
    const email = await createStudent();
    await loginViaForm(page, email, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);
    const dump = await page.evaluate(() => JSON.stringify({ ...localStorage, ...sessionStorage }) + document.cookie);
    expect(dump).not.toContain(PASSWORD);
  });

  test("remember me ON: session survives a browser restart", async ({ page, browser }) => {
    const email = await createStudent();
    await loginViaForm(page, email, PASSWORD, true);
    await expect(page).toHaveURL(/\/dashboard/);
    expect(await page.evaluate(() => localStorage.getItem("vizu_refresh_token"))).toBeTruthy();

    // a new context only gets persistent storage (localStorage), like a reopened browser
    const reopened = await browser.newContext({ storageState: await page.context().storageState() });
    const again = await reopened.newPage();
    await again.goto("/");
    await expect(again).toHaveURL(/\/dashboard/);
    await reopened.close();
  });

  test("remember me OFF: session ends with the browser", async ({ page, browser }) => {
    const email = await createStudent();
    await loginViaForm(page, email, PASSWORD, false);
    await expect(page).toHaveURL(/\/dashboard/);
    expect(await page.evaluate(() => localStorage.getItem("vizu_refresh_token"))).toBeNull();
    expect(await page.evaluate(() => sessionStorage.getItem("vizu_refresh_token"))).toBeTruthy();

    const reopened = await browser.newContext({ storageState: await page.context().storageState() });
    const again = await reopened.newPage();
    await again.goto("/dashboard");
    await expect(again).toHaveURL(/\/login/);
    await reopened.close();
  });

  test("protected page without a session asks for login", async ({ page }) => {
    await page.goto("/settings");
    await expect(page).toHaveURL(/\/login/);
  });
});

test.describe("logout", () => {
  test("header logout revokes the refresh token server-side and blocks Back", async ({ page, isMobile }) => {
    test.skip(isMobile, "header avatar menu is the desktop path; mobile has its own test");
    const email = await createStudent();
    await loginViaForm(page, email, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);
    const refresh = await page.evaluate(() => localStorage.getItem("vizu_refresh_token"));
    // leave /dashboard in the history, so Back has a protected page to go to
    await page.goto("/settings");

    await page.getByRole("button", { name: /E2E|Zayniddin|Lernende|Learner/i }).first().click();
    await page.getByRole("menuitem", { name: "Abmelden" }).click();
    await expect(page).toHaveURL(/\/login/);
    expect(await page.evaluate(() => localStorage.getItem("vizu_refresh_token"))).toBeNull();

    // server side: the refresh token no longer works
    await expect.poll(async () => (await fetch(`${API_URL}/auth/refresh`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh_token: refresh }),
    })).status).toBe(401);

    // Back reaches /dashboard in the history: it must not render, the guard sends to /login
    await page.goBack();
    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole("button", { name: "Anmelden" })).toBeVisible();
  });

  test("mobile menu has a logout button that ends the session", async ({ page, isMobile }) => {
    test.skip(!isMobile, "mobile navigation only");
    const email = await createStudent();
    await loginViaForm(page, email, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);
    await page.getByRole("button", { name: "Menü öffnen" }).click();
    const logout = page.getByTestId("mobile-logout");
    await expect(logout).toBeVisible();
    await expect(logout).toHaveText(/Abmelden/);
    await logout.click();
    await expect(page).toHaveURL(/\/login/);
    expect(await page.evaluate(() => localStorage.getItem("vizu_access_token"))).toBeNull();
  });
});
