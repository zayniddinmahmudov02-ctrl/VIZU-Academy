import { expect, test, type Page } from "@playwright/test";

import { ADMIN, API_URL, apiToken, createStudent, loginViaForm } from "./helpers";

/** Admin student statistics: the dashboard shows exactly the API / database number, a new registration adds one after a
 * refresh, the list total equals the big number, filters add up, and the block fits a phone screen. Local stack only. */

const fmt = (n: number) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ");

async function overview(token: string) {
  const res = await fetch(`${API_URL}/api/v1/admin/stats/overview`, { headers: { Authorization: `Bearer ${token}` } });
  expect(res.status).toBe(200);
  return res.json();
}

/** A registration through the public API with a normal domain (createStudent() uses example.com = a test account). */
async function registerRealLooking(): Promise<string> {
  const email = `stat_${Date.now()}_${Math.floor(Math.random() * 1e6)}@e2e-mail.uz`;
  const res = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Forwarded-For": `10.79.${Math.floor(Math.random() * 250)}.${Math.floor(Math.random() * 250)}` },
    body: JSON.stringify({ full_name: "Stat Talaba", identifier: email, password: "Geheim123!", password_confirm: "Geheim123!" }),
  });
  expect(res.status, await res.clone().text()).toBe(200);
  return email;
}

async function loginAdmin(page: Page) {
  await loginViaForm(page, ADMIN.email, ADMIN.password);
  await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
  await page.getByRole("button", { name: "Bestätigen" }).click();
  await expect(page).toHaveURL(/\/admin/);
}

test("dashboard shows the database count and grows by one per registration", async ({ page, isMobile }) => {
  test.skip(isMobile, "desktop flow; the phone layout is checked below");
  const token = await apiToken(ADMIN.email, ADMIN.password);
  await loginAdmin(page);
  await page.goto("/admin");
  const before = await overview(token);
  await expect(page.getByTestId("stat-total-students")).toHaveText(fmt(before.total_students), { timeout: 20_000 });
  await expect(page.getByTestId("stat-active-students")).toHaveText(fmt(before.active_students));
  await expect(page.getByTestId("stat-inactive-students")).toHaveText(fmt(before.inactive_students));
  expect(before.active_students + before.inactive_students).toBe(before.total_students);

  // a test account (example.com) is shown separately and never enters the student total
  await createStudent();
  const withTest = await overview(token);
  expect(withTest.total_students).toBe(before.total_students);
  expect(withTest.test_accounts).toBe(before.test_accounts + 1);

  await registerRealLooking(); // a real registration through the public API
  await page.getByRole("button", { name: "Aktualisieren" }).click();
  await expect(page.getByTestId("stat-total-students")).toHaveText(fmt(before.total_students + 1), { timeout: 20_000 });
  const after = await overview(token);
  expect(after.total_students).toBe(before.total_students + 1);
  expect(after.total_registrations_today).toBe(before.total_registrations_today + 1);
  expect(after.total_teachers).toBe(before.total_teachers);
  expect(after.total_admins).toBe(before.total_admins);
  await expect(page.getByTestId("stat-new-today")).toHaveText(fmt(after.total_registrations_today));

  // the list counts the same students: total = the big number, active + inactive = all
  await page.getByTestId("student-list-toggle").click();
  await expect(page.getByTestId("student-list-total")).toHaveText(fmt(after.total_students));
  await page.getByTestId("student-list-tab-active").click();
  await expect(page.getByTestId("student-list-total")).toHaveText(fmt(after.active_students));
  await page.getByTestId("student-list-tab-inactive").click();
  await expect(page.getByTestId("student-list-total")).toHaveText(fmt(after.inactive_students));
  await page.getByTestId("student-list-tab-all").click();
  await expect(page.getByTestId("student-row")).toHaveCount(Math.min(20, after.total_students));
});

test("students cannot read the statistics", async () => {
  const email = await createStudent();
  const token = await apiToken(email, "Geheim123!");
  for (const path of ["/api/v1/admin/stats/overview", "/api/v1/admin/stats/students"]) {
    const res = await fetch(`${API_URL}${path}`, { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status, path).toBe(403);
    expect((await fetch(`${API_URL}${path}`)).status, path).toBe(401);
  }
});

test("the statistics block fits a phone screen", async ({ page, isMobile }) => {
  test.skip(!isMobile, "phone only");
  await loginAdmin(page);
  await page.goto("/admin");
  await expect(page.getByTestId("stat-total-students")).toBeVisible({ timeout: 20_000 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1);
});
