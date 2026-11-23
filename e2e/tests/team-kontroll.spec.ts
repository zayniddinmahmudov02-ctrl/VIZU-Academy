import { expect, test, type Page } from "@playwright/test";

import { ADMIN, API_URL, apiToken, loginViaForm, useLanguage } from "./helpers";

/** Admin → Team → new teacher (login + temporary password, Kontroll "Nein") → first login forces an own password → empty Teacher
 * Panel with all sections, no Kontroll → the admin gives a group (the student in it appears once in Schüler) and Kontroll →
 * Kontroll lists every student read-only with server-measured times (two real heartbeats) and the timeline → the student sees
 * the Medien statistics. Local stack only (never production: it creates accounts). */

test.describe.configure({ mode: "serial" });

const TAG = Date.now().toString(36);
const TEACHER = { username: `t_e2e_${TAG}`, name: `Lehrkraft E2E ${TAG}`, password: "", own: "EigenesPw2026x" };
const STUDENT = { email: `kontroll_${TAG}@e2e-mail.uz`, password: "Geheim123!" };
let teacherId = "";
let groupId = "";

async function api(method: string, path: string, token: string, body?: unknown) {
  const res = await fetch(`${API_URL}/api/v1${path}`, {
    method, headers: { Authorization: `Bearer ${token}`, ...(body ? { "Content-Type": "application/json" } : {}) }, body: body ? JSON.stringify(body) : undefined,
  });
  return { status: res.status, json: await res.json().catch(() => null) };
}

async function loginAdmin(page: Page) {
  await loginViaForm(page, ADMIN.email, ADMIN.password);
  await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
  await page.getByRole("button", { name: "Bestätigen" }).click();
  await expect(page).toHaveURL(/\/admin/);
}

async function noSideScroll(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(1);
}

test.beforeAll(async () => {
  const reg = await fetch(`${API_URL}/auth/register`, {
    method: "POST", headers: { "Content-Type": "application/json", "X-Forwarded-For": `10.81.${Math.floor(Math.random() * 250)}.${Math.floor(Math.random() * 250)}` },
    body: JSON.stringify({ full_name: "Kontroll Talaba", identifier: STUDENT.email, password: STUDENT.password, password_confirm: STUDENT.password }),
  });
  expect(reg.status, await reg.clone().text()).toBe(200);
  // a group of the Super Admin with the student in it (joined with the real code)
  const admin = await apiToken(ADMIN.email, ADMIN.password);
  const created = await api("POST", "/groups", admin, { name: `Kontroll ${TAG}`, level: "A2" });
  expect(created.status, JSON.stringify(created.json)).toBe(201);
  groupId = created.json.group.id;
  const student = await apiToken(STUDENT.email, STUDENT.password);
  expect((await api("POST", "/groups/join", student, { code: created.json.code })).status).toBe(200);
});

test("admin creates a teacher with a temporary password (Kontroll: Nein by default)", async ({ page, isMobile }) => {
  test.skip(isMobile, "desktop flow; the phone layout is checked at the end");
  await useLanguage(page, "de");
  await loginAdmin(page);
  await page.goto("/admin/team");
  await expect(page.getByTestId("admin-team")).toBeVisible();
  const before = Number(await page.getByTestId("team-total").innerText().catch(() => "0")) || 0;
  await page.getByTestId("team-add").click();
  await page.getByTestId("teacher-full-name").fill(TEACHER.name);
  await page.getByTestId("teacher-username").fill(TEACHER.username);
  await expect(page.getByTestId("kontroll-no")).toBeChecked();
  await expect(page.getByTestId("kontroll-question")).toContainText("Darf dieser Lehrer auf den Bereich „Kontroll“ zugreifen?");
  await page.getByTestId("create-teacher-submit").click();
  await expect(page.getByTestId("password-result")).toBeVisible();
  await expect(page.getByTestId("result-username")).toHaveText(TEACHER.username);
  TEACHER.password = (await page.getByTestId("result-password").innerText()).trim();
  expect(TEACHER.password.length).toBeGreaterThanOrEqual(14);
  await page.getByTestId("password-result-close").click();
  await page.getByTestId("team-search").fill(TEACHER.username);
  const row = page.getByRole("row").filter({ hasText: TEACHER.username });
  await expect(row).toBeVisible();
  await expect(row.getByTestId("team-control-no")).toBeVisible();
  await expect.poll(async () => Number(await page.getByTestId("team-total").innerText())).toBeGreaterThanOrEqual(before + 1);
  // the same username again is refused
  await page.getByTestId("team-add").click();
  await page.getByTestId("teacher-full-name").fill("Zweite Lehrkraft");
  await page.getByTestId("teacher-username").fill(TEACHER.username);
  await page.getByTestId("create-teacher-submit").click();
  await expect(page.getByTestId("create-teacher-error")).toContainText("bereits vergeben");
  const admin = await apiToken(ADMIN.email, ADMIN.password);
  const list = await api("GET", `/admin/team/teachers?search=${TEACHER.username}`, admin);
  teacherId = list.json.items[0].id;
  expect(list.json.items[0].must_change_password).toBe(true);
});

test("first login: own password first, then the empty Teacher Panel without Kontroll", async ({ page, isMobile }) => {
  test.skip(isMobile, "desktop flow");
  await useLanguage(page, "de");
  await loginViaForm(page, TEACHER.username, TEACHER.password);
  await expect(page.getByTestId("password-gate")).toBeVisible({ timeout: 20_000 });
  const blocked = await api("GET", "/teacher/dashboard", await apiToken(TEACHER.username, TEACHER.password));
  expect(blocked.status).toBe(403);
  await page.getByTestId("pw-current").fill(TEACHER.password);
  await page.getByTestId("pw-new").fill(TEACHER.password);
  await page.getByTestId("pw-repeat").fill(TEACHER.password);
  await page.getByTestId("pw-save").click();
  await expect(page.getByTestId("pw-error")).toBeVisible();
  await page.getByTestId("pw-new").fill(TEACHER.own);
  await page.getByTestId("pw-repeat").fill(TEACHER.own);
  await page.getByTestId("pw-save").click();
  await expect(page.getByTestId("password-gate-done")).toBeVisible();

  await loginViaForm(page, TEACHER.username, TEACHER.own);
  await expect(page).toHaveURL(/\/teacher$/, { timeout: 20_000 });
  await expect(page.getByTestId("teacher-dashboard")).toBeVisible();
  await expect(page.getByTestId("teacher-no-group")).toBeVisible();
  await expect(page.getByTestId("stat-students-value")).toHaveText("0");
  const nav = page.locator("aside").getByTestId("teacher-nav");
  for (const name of ["Dashboard", "Schüler", "Gruppen", "Kurse", "Unterricht", "Aufgaben", "Hausaufgaben", "Prüfungen", "Materialien", "Nachrichten", "Einstellungen"]) {
    await expect(nav.getByRole("link", { name, exact: true })).toBeVisible();
  }
  await expect(nav.getByRole("link", { name: "Kontroll" })).toHaveCount(0);
  for (const [path, text] of [["/teacher/students", "Noch keine Schüler zugewiesen."], ["/teacher/kurse", "Noch keine Kurse zugewiesen."],
                              ["/teacher/aufgaben", "Noch keine Aufgaben vergeben."], ["/teacher/kontroll", "keinen Zugriff"]]) {
    await page.goto(path);
    await expect(page.getByText(text)).toBeVisible({ timeout: 20_000 });
  }
  const token = await apiToken(TEACHER.username, TEACHER.own);
  expect((await api("GET", "/teacher/kontroll/students", token)).status).toBe(403);
  expect((await api("PUT", `/admin/team/teachers/${teacherId}/control`, token, { enabled: true })).status).toBe(403);
});

test("admin assigns the group and Kontroll; the teacher sees the student once and Kontroll read-only", async ({ page, browser, isMobile }) => {
  test.skip(isMobile, "desktop flow");
  test.setTimeout(120_000);
  await useLanguage(page, "de");
  await loginAdmin(page);
  await page.goto("/admin/team");
  await page.getByTestId("team-search").fill(TEACHER.username);
  await page.getByRole("row").filter({ hasText: TEACHER.username }).getByTestId("team-open").click();
  await expect(page.getByTestId("teacher-detail")).toBeVisible();
  await page.getByTestId("assign-group-select").selectOption(groupId);
  await page.getByTestId("assign-group").click();
  await expect(page.getByTestId("team-notice")).toHaveText("Gespeichert.");
  await page.getByTestId("toggle-kontroll").click();
  await page.getByRole("button", { name: "Bestätigen" }).click();
  await expect(page.getByTestId("detail-kontroll")).toContainText("Ja — Kontroll aktiv");
  await expect(page.getByTestId("teacher-history")).toContainText("Nein → Ja");

  // two real heartbeats of the student, 12 s apart on the server clock (Wortschatz page)
  const student = await apiToken(STUDENT.email, STUDENT.password);
  const beat = { tab_id: `e2etab${TAG}`, active: true, contexts: [{ area: "WORTSCHATZ", ref_id: null, position: null }] };
  expect((await api("POST", "/activity/heartbeat", student, beat)).json.credited).toBe(0);
  await page.waitForTimeout(12_000);
  const second = await api("POST", "/activity/heartbeat", student, beat);
  expect(second.json.credited).toBeGreaterThanOrEqual(11);

  const teacherPage = await (await browser.newContext()).newPage();
  await useLanguage(teacherPage, "de");
  await loginViaForm(teacherPage, TEACHER.username, TEACHER.own);
  await expect(teacherPage).toHaveURL(/\/teacher$/, { timeout: 20_000 });
  await expect(teacherPage.getByTestId("stat-students-value")).toHaveText("1");
  await teacherPage.goto("/teacher/students");
  await expect(teacherPage.getByTestId("roster-row")).toHaveCount(1);
  await expect(teacherPage.getByTestId("roster-row")).toContainText(`Kontroll ${TAG}`);
  await teacherPage.getByTestId("roster-row").getByRole("link").click();
  await expect(teacherPage.getByTestId("teacher-student-profile")).toContainText(STUDENT.email);

  const nav = teacherPage.locator("aside").getByTestId("teacher-nav");
  await expect(nav.getByRole("link", { name: "Kontroll" })).toBeVisible();
  await teacherPage.goto("/teacher/kontroll");
  await expect(teacherPage.getByTestId("kontroll")).toBeVisible();
  await teacherPage.getByTestId("kontroll-search").fill(STUDENT.email);
  const row = teacherPage.getByTestId("kontroll-row");
  await expect(row).toHaveCount(1, { timeout: 20_000 });
  await expect(row).toContainText(/1\d Sek\./);
  await row.getByRole("link").click();
  await expect(teacherPage.getByTestId("kontroll-general")).toBeVisible();
  await expect(teacherPage.getByTestId("k-total")).toContainText("Sek.");
  await expect(teacherPage.getByTestId("timeline-item").first()).toContainText("Wortschatz");
  await expect(teacherPage.getByText("Nur Ansicht").first()).toBeVisible();
  const token = await apiToken(TEACHER.username, TEACHER.own);
  const sid = (await api("GET", `/teacher/kontroll/students?search=${encodeURIComponent(STUDENT.email)}`, token)).json.items[0].id;
  expect((await api("DELETE", `/teacher/kontroll/students/${sid}`, token)).status).toBe(405);
  await teacherPage.context().close();
});

test("the student sees the own Medien statistics with the privacy note", async ({ page, isMobile }) => {
  test.skip(isMobile, "desktop flow");
  await useLanguage(page, "de");
  await loginViaForm(page, STUDENT.email, STUDENT.password);
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 20_000 });
  await page.goto("/medien");
  await expect(page.getByTestId("medien-stats")).toBeVisible({ timeout: 20_000 });
  for (const id of ["stat-music", "stat-books", "stat-films", "stat-usage"]) await expect(page.getByTestId(id)).toBeVisible();
  await expect(page.getByTestId("stat-music")).toContainText("Musik gehört");
  await expect(page.getByTestId("stat-books")).toContainText("Bücher angesehen");
  await expect(page.getByTestId("stat-films")).toContainText("Filme angesehen");
  await page.getByTestId("medien-stats-privacy").locator("summary").click();
  await expect(page.getByTestId("medien-stats-privacy")).toContainText("Kontroll");
  await page.goto("/medien/musik");
  await page.waitForTimeout(1200);
  await page.getByTestId("medien-section-stats-music-toggle").click();
  await expect(page.getByTestId("medien-section-stats-music")).toContainText("Du hast noch keine Lieder gehört.");
});

test.describe("Teacher Panel on a phone", () => {
  test.skip(({ isMobile }) => !isMobile, "phone layout");
  test("menu drawer, Kontroll and Team fit the screen", async ({ page }) => {
    test.setTimeout(90_000);
    // runs after the desktop project in the same local DB; make sure the teacher exists with its own password
    const admin = await apiToken(ADMIN.email, ADMIN.password);
    const found = await api("GET", "/admin/team/teachers?search=t_e2e_", admin);
    test.skip(!found.json?.items?.length, "needs the desktop run first");
    const t = found.json.items.find((x: { must_change_password: boolean; can_access_student_control: boolean }) => !x.must_change_password && x.can_access_student_control);
    test.skip(!t, "needs the desktop run first");
    const reset = await api("POST", `/admin/team/teachers/${t.id}/reset-password`, admin, { password: "PhonePw2026xy" });
    expect(reset.status).toBe(200);
    const login = await apiToken(t.username, "PhonePw2026xy");
    expect((await fetch(`${API_URL}/api/v1/users/me/password`, { method: "PUT", headers: { Authorization: `Bearer ${login}`, "Content-Type": "application/json" },
                                                             body: JSON.stringify({ current_password: "PhonePw2026xy", new_password: "PhonePw2026zz" }) })).status).toBe(200);
    await useLanguage(page, "de");
    await loginViaForm(page, t.username, "PhonePw2026zz");
    await expect(page).toHaveURL(/\/teacher$/, { timeout: 20_000 });
    await noSideScroll(page);
    await page.getByTestId("teacher-menu-button").click();
    const drawer = page.getByRole("dialog", { name: "Menü" });
    await expect(drawer.getByRole("link", { name: "Kontroll" })).toBeVisible();
    await drawer.getByRole("link", { name: "Kontroll" }).click();
    await expect(page.getByTestId("kontroll")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByRole("dialog", { name: "Menü" })).toHaveCount(0);
    await noSideScroll(page);
    await page.goto("/teacher/students");
    await expect(page.getByTestId("teacher-students")).toBeVisible();
    await noSideScroll(page);
  });
});
