import { expect, type Page } from "@playwright/test";

export const API_URL = process.env.E2E_API_URL ?? "http://127.0.0.1:8000";
export const PASSWORD = "Geheim123!";
export const ADMIN = {
  email: process.env.E2E_ADMIN_EMAIL ?? "e2e-admin@example.com",
  password: process.env.E2E_ADMIN_PASSWORD ?? "AdminE2E123",
  verify: process.env.E2E_ADMIN_VERIFY ?? "e2e-admin-check",
};

let counter = 0;

/** Creates a fresh student over the real API. Each call uses its own
 * X-Forwarded-For so the per-IP registration limit (10/h) is not hit by the
 * test run itself (test backend only). */
export async function createStudent(): Promise<string> {
  const email = `e2e_${Date.now()}_${counter++}@example.com`;
  const res = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Forwarded-For": `10.77.${counter}.${Math.floor(Math.random() * 250)}` },
    body: JSON.stringify({ full_name: "E2E Student", identifier: email, password: PASSWORD, password_confirm: PASSWORD }),
  });
  expect(res.status, await res.clone().text()).toBe(200);
  return email;
}

export async function useLanguage(page: Page, language: "de" | "uz") {
  await page.addInitScript((lang) => {
    localStorage.setItem("vizu-language", JSON.stringify({ state: { language: lang }, version: 0 }));
  }, language);
}

export async function loginViaForm(page: Page, email: string, password: string, remember = true) {
  await page.goto("/login");
  await page.getByPlaceholder("E-Mail oder +998 90 123 45 67").fill(email);
  await page.getByPlaceholder("Passwort", { exact: true }).fill(password);
  const box = page.getByRole("checkbox", { name: "Angemeldet bleiben" });
  if ((await box.isChecked()) !== remember) await box.click();
  await page.getByRole("button", { name: "Anmelden" }).click();
}
