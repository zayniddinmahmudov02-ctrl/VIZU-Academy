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

/** Bearer token over the real login API (own X-Forwarded-For per call, like createStudent). */
export async function apiToken(identifier: string, password: string): Promise<string> {
  const res = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Forwarded-For": `10.78.${counter++ % 250}.${Math.floor(Math.random() * 250)}` },
    body: JSON.stringify({ identifier, password }),
  });
  expect(res.status, await res.clone().text()).toBe(200);
  return (await res.json()).access_token as string;
}

async function apiCall(method: string, path: string, bearer: string, body?: unknown) {
  const res = await fetch(`${API_URL}/api/v1${path}`, {
    method, headers: { Authorization: `Bearer ${bearer}`, ...(body ? { "Content-Type": "application/json" } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  return { status: res.status, json: await res.json().catch(() => null) };
}

/** Since 2026-11-16 every Multilevel Modelltest needs the Multilevel Premium. Grants it the real way: the Super Admin creates a 100 %
 * Multilevel promo code (PENDING), approves + activates it, the student redeems it (local stack only). */
export async function grantMultilevelPremium(studentEmail: string): Promise<void> {
  const admin = await apiToken(ADMIN.email, ADMIN.password);
  const code = `E2EML${Date.now().toString(36).toUpperCase()}${counter++}`;
  const created = await apiCall("POST", "/admin/vizu-pay/promo-codes", admin, {
    code, discount_type: "FREE_ACCESS", discount_value: 100, applicable_course_ids: [], applicable_package_codes: [], max_uses: 1,
    max_uses_per_user: 1, product_category: "MULTILEVEL",
  });
  expect(created.status, JSON.stringify(created.json)).toBe(200);
  expect((await apiCall("POST", `/admin/vizu-pay/promo-codes/${created.json.id}/review`, admin, { action: "approve_activate" })).status).toBe(200);
  const student = await apiToken(studentEmail, PASSWORD);
  const redeemed = await apiCall("POST", "/vizu-pay/multilevel/redeem", student, { code });
  expect(redeemed.status, JSON.stringify(redeemed.json)).toBe(200);
  expect(redeemed.json.entitled).toBe(true);
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
