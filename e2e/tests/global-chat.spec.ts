import { expect, test, type Page } from "@playwright/test";

import { ADMIN, API_URL, loginViaForm, useLanguage } from "./helpers";

// Global Chat against the throwaway stack (README.md). Needs these users in the
// test database (D:\vz_tmp\work\gc_seed.py creates them and empties the chat):
//   e2e-admin@example.com (SUPER_ADMIN), gc-student1@ / gc-student2@ (STUDENT),
//   gc-teacher@example.com (TEACHER), all with password Geheim123! except the admin.
const STUDENT1 = "gc-student1@example.com";
const STUDENT2 = "gc-student2@example.com";
const TEACHER = "gc-teacher@example.com";
const PASSWORD = "Geheim123!";

async function apiToken(identifier: string, password: string): Promise<string> {
  const res = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ identifier, password }),
  });
  expect(res.status, await res.clone().text()).toBe(200);
  return (await res.json()).access_token;
}

async function apiPost(token: string, body: string) {
  return fetch(`${API_URL}/api/v1/global-chat/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ body }),
  });
}

async function openChat(page: Page) {
  await page.getByTestId("global-chat-button").click();
  await expect(page.getByTestId("global-chat-panel")).toBeVisible();
}

test.describe("Global Chat", () => {
  test("anonymous API calls are refused", async () => {
    for (const path of ["/api/v1/global-chat/messages", "/api/v1/global-chat/unread-count", "/api/v1/admin/global-chat/restrictions"]) {
      const res = await fetch(`${API_URL}${path}`);
      expect(res.status, path).toBe(401);
    }
    const post = await fetch(`${API_URL}/api/v1/global-chat/messages`, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{\"body\":\"x\"}" });
    expect(post.status).toBe(401);
  });

  test("a student can not use moderation endpoints", async () => {
    const token = await apiToken(STUDENT2, PASSWORD);
    const sent = await apiPost(token, `Hallo ${Date.now()}`);
    expect(sent.status).toBe(201);
    const message = await sent.json();
    const headers = { "Content-Type": "application/json", Authorization: `Bearer ${token}` };
    const pin = await fetch(`${API_URL}/api/v1/admin/global-chat/messages/${message.id}`, { method: "PATCH", headers, body: JSON.stringify({ action: "pin" }) });
    expect(pin.status).toBe(403);
    const ban = await fetch(`${API_URL}/api/v1/admin/global-chat/restrictions`, {
      method: "POST", headers, body: JSON.stringify({ user_id: message.sender.id, kind: "ban", duration: "1y", reason: "test" }),
    });
    expect(ban.status).toBe(403);
  });

  test("student sends a message; HTML is shown as text and never runs", async ({ page }) => {
    await useLanguage(page, "de");
    let dialogs = 0;
    page.on("dialog", (d) => {
      dialogs++;
      d.dismiss();
    });
    await loginViaForm(page, STUDENT1, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);
    await openChat(page);

    const evil = `<img src=x onerror="alert('xss')"><script>alert(1)</script> ${Date.now()}`;
    const input = page.getByTestId("global-chat-input");
    await input.fill(evil);
    await input.press("Enter");
    const mine = page.getByTestId("global-chat-message").filter({ hasText: "<script>alert(1)</script>" });
    await expect(mine).toBeVisible();
    await expect(page.locator("[data-testid=global-chat-list] img, [data-testid=global-chat-list] script")).toHaveCount(0);
    expect(dialogs).toBe(0);
    await expect(input).toHaveValue("");
    await page.waitForTimeout(1100); // the server allows one message per second

    // Shift+Enter makes a new line instead of sending
    await input.fill("Zeile 1");
    await input.press("Shift+Enter");
    await input.pressSequentially("Zeile 2");
    await expect(input).toHaveValue("Zeile 1\nZeile 2");
    await page.getByTestId("global-chat-send").click();
    await expect(page.getByTestId("global-chat-message").filter({ hasText: "Zeile 2" })).toBeVisible();

    // empty messages can not be sent
    await input.fill("   ");
    await expect(page.getByTestId("global-chat-send")).toBeDisabled();
  });

  test("teacher sees the student's message live and the unread badge", async ({ page }) => {
    await useLanguage(page, "de");
    await loginViaForm(page, TEACHER, PASSWORD);
    await expect(page).not.toHaveURL(/\/login/);
    await page.goto("/teacher");
    await expect(page.getByTestId("global-chat-button")).toBeVisible();
    await openChat(page);
    await page.getByTestId("global-chat-close").click();

    const token = await apiToken(STUDENT2, PASSWORD);
    const text = `Ungelesen ${Date.now()}`;
    expect((await apiPost(token, text)).status).toBe(201);
    await page.reload();
    await expect(page.getByTestId("global-chat-badge")).toHaveText(/^[1-9]\d*\+?$/, { timeout: 15_000 });

    await openChat(page);
    await expect(page.getByTestId("global-chat-message").filter({ hasText: text })).toBeVisible();
    // a new message arrives while the window is open (polling)
    const live = `Live ${Date.now()}`;
    await new Promise((r) => setTimeout(r, 1100)); // the sender's own 1-second spacing
    expect((await apiPost(token, live)).status).toBe(201);
    await expect(page.getByTestId("global-chat-message").filter({ hasText: live })).toBeVisible({ timeout: 10_000 });
    await page.getByTestId("global-chat-close").click();
    await expect(page.getByTestId("global-chat-badge")).toHaveCount(0);
  });

  test("admin pins a message and mutes a student; the student reads but can not write", async ({ page, browser }) => {
    await useLanguage(page, "de");
    const studentToken = await apiToken(STUDENT1, PASSWORD);
    const text = `Bitte anheften ${Date.now()}`;
    expect((await apiPost(studentToken, text)).status).toBe(201);

    await loginViaForm(page, ADMIN.email, ADMIN.password);
    await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
    await page.getByRole("button", { name: "Bestätigen" }).click();
    await expect(page).toHaveURL(/\/admin/);
    await openChat(page);
    const msg = page.getByTestId("global-chat-message").filter({ hasText: text });
    await msg.getByRole("button", { name: "Anheften" }).click();
    await expect(page.getByTestId("global-chat-pinned")).toContainText(text);

    await msg.getByRole("button", { name: "Stummschalten" }).click();
    const dialog = page.getByTestId("gc-restrict-dialog");
    await dialog.getByLabel("10 Minuten").check();
    await dialog.getByPlaceholder(/wiederholte Beleidigungen/).fill("E2E: Test-Stummschaltung");
    await dialog.getByPlaceholder(/respektvoll/).fill("Bitte respektvoll bleiben.");
    await dialog.getByRole("button", { name: "Stummschalten" }).last().click();
    await expect(dialog).toHaveCount(0);

    // the ban dialog offers 1 year and shows the calendar end date
    await msg.getByRole("button", { name: "Sperren" }).click();
    await expect(page.getByTestId("gc-restrict-dialog").getByLabel("1 Jahr")).toBeChecked();
    const end = await page.getByTestId("gc-restrict-end").innerText();
    const now = new Date();
    expect(end).toContain(`${String(now.getDate()).padStart(2, "0")}.${String(now.getMonth() + 1).padStart(2, "0")}.${now.getFullYear() + 1}`);
    await page.getByTestId("gc-restrict-dialog").getByRole("button", { name: "Abbrechen" }).click();

    // the student: pinned message on top, history readable, input replaced by the notice
    const context = await browser.newContext();
    const studentPage = await context.newPage();
    await useLanguage(studentPage, "de");
    await loginViaForm(studentPage, STUDENT1, PASSWORD);
    await expect(studentPage).toHaveURL(/\/dashboard/);
    await openChat(studentPage);
    await expect(studentPage.getByTestId("global-chat-pinned")).toContainText(text);
    await expect(studentPage.getByTestId("global-chat-message").filter({ hasText: text })).toBeVisible();
    await expect(studentPage.getByTestId("global-chat-restricted")).toContainText("stummgeschaltet");
    await expect(studentPage.getByTestId("global-chat-restricted")).toContainText("Bitte respektvoll bleiben.");
    await expect(studentPage.getByTestId("global-chat-input")).toHaveCount(0);
    // and the server refuses, whatever the UI shows
    expect((await apiPost(studentToken, "trotzdem")).status).toBe(403);
    // the rest of the platform still works
    await studentPage.getByTestId("global-chat-close").click();
    await studentPage.goto("/kurse");
    await expect(studentPage).toHaveURL(/\/kurse/);
    await context.close();

    // admin lifts the mute on /admin/global-chat
    await page.goto("/admin/global-chat");
    await page.getByRole("tab", { name: /Mutes & Sperren/ }).click();
    const row = page.getByTestId("gc-restriction-row").filter({ hasText: "Sami" });
    await row.getByRole("button", { name: /Aufheben/ }).click();
    await page.getByRole("dialog").getByRole("button", { name: "Aufheben" }).click();
    await expect(page.getByRole("status")).toContainText("aufgehoben");
    expect((await apiPost(studentToken, `wieder da ${Date.now()}`)).status).toBe(201);
  });

  test("edit / delete endpoints: login required, only the author", async () => {
    const fake = "00000000-0000-0000-0000-000000000000";
    for (const method of ["PATCH", "DELETE"]) {
      const res = await fetch(`${API_URL}/api/v1/global-chat/messages/${fake}`, {
        method, headers: { "Content-Type": "application/json" }, body: method === "PATCH" ? "{\"body\":\"x\"}" : undefined,
      });
      expect(res.status, method).toBe(401);
    }
    const author = await apiToken(STUDENT1, PASSWORD);
    const other = await apiToken(STUDENT2, PASSWORD);
    await new Promise((r) => setTimeout(r, 1100)); // the author may have written a moment ago (1 message / second)
    const sent = await apiPost(author, `Eigentum ${Date.now()}`);
    expect(sent.status).toBe(201);
    const { id } = await sent.json();
    const headers = (token: string) => ({ "Content-Type": "application/json", Authorization: `Bearer ${token}` });
    const edit = await fetch(`${API_URL}/api/v1/global-chat/messages/${id}`, { method: "PATCH", headers: headers(other), body: JSON.stringify({ body: "fremd" }) });
    expect(edit.status).toBe(403);
    const del = await fetch(`${API_URL}/api/v1/global-chat/messages/${id}`, { method: "DELETE", headers: headers(other) });
    expect(del.status).toBe(403);
    const smuggle = await fetch(`${API_URL}/api/v1/global-chat/messages/${id}`, {
      method: "PATCH", headers: headers(other), body: JSON.stringify({ body: "fremd", sender_id: "x" }),
    });
    expect(smuggle.status).toBe(422);
    const tooLong = await fetch(`${API_URL}/api/v1/global-chat/messages/${id}`, { method: "PATCH", headers: headers(author), body: JSON.stringify({ body: "x".repeat(2001) }) });
    expect(tooLong.status).toBe(422);
    const own = await fetch(`${API_URL}/api/v1/global-chat/messages/${id}`, { method: "DELETE", headers: headers(author) });
    expect(own.status).toBe(204);
  });

  test("author edits and deletes; the other user's window follows", async ({ page, browser }) => {
    // the teacher is the author here: the students already used much of their 10-messages-a-minute quota above
    await useLanguage(page, "de");
    await loginViaForm(page, TEACHER, PASSWORD);
    await expect(page).not.toHaveURL(/\/login/);
    await expect(page.getByTestId("global-chat-button")).toBeVisible();
    await openChat(page);

    const reader = await browser.newContext();
    const readerPage = await reader.newPage();
    await useLanguage(readerPage, "de");
    await loginViaForm(readerPage, STUDENT2, PASSWORD);
    await expect(readerPage).toHaveURL(/\/dashboard/);
    await openChat(readerPage);

    const original = `Tippfeler ${Date.now()}`;
    const input = page.getByTestId("global-chat-input");
    await input.fill(original);
    await input.press("Enter");
    const mine = page.getByTestId("global-chat-message").filter({ hasText: original });
    await expect(mine).toBeVisible();
    await expect(readerPage.getByTestId("global-chat-message").filter({ hasText: original })).toBeVisible({ timeout: 10_000 });
    // nobody gets a menu on someone else's message
    await expect(readerPage.getByTestId("global-chat-message").filter({ hasText: original }).getByTestId("global-chat-message-menu")).toHaveCount(0);

    // edit: menu → Bearbeiten → textarea with the text → Escape cancels, Enter saves
    await mine.getByTestId("global-chat-message-menu").click();
    await page.getByRole("menuitem", { name: "Bearbeiten" }).click();
    const editor = page.getByTestId("global-chat-edit-input");
    await expect(editor).toHaveValue(original);
    await editor.press("Escape");
    await expect(editor).toHaveCount(0);
    await expect(page.getByTestId("global-chat-panel")).toBeVisible();  // Escape closed only the editor

    await mine.getByTestId("global-chat-message-menu").click();
    await page.getByRole("menuitem", { name: "Bearbeiten" }).click();
    await editor.fill("");
    await expect(page.getByTestId("global-chat-edit-save")).toBeDisabled();
    const fixed = `${original.replace("Tippfeler", "Tippfehler")} <b>fett</b>`;
    await editor.fill(fixed);
    await editor.press("Enter");
    const edited = page.getByTestId("global-chat-message").filter({ hasText: fixed });
    await expect(edited).toBeVisible();
    await expect(edited.getByTestId("global-chat-edited")).toHaveText("bearbeitet");
    await expect(edited.locator("b")).toHaveCount(0);  // shown as text
    const readerEdited = readerPage.getByTestId("global-chat-message").filter({ hasText: fixed });
    await expect(readerEdited).toBeVisible({ timeout: 10_000 });
    await expect(readerEdited.getByTestId("global-chat-edited")).toBeVisible();

    // the menu stays inside the window, also for the last message
    await edited.getByTestId("global-chat-message-menu").click();
    const menu = page.getByRole("menu");
    const box = (await menu.boundingBox())!;
    const panel = (await page.getByTestId("global-chat-panel").boundingBox())!;
    expect(box.x).toBeGreaterThanOrEqual(panel.x);
    expect(box.x + box.width).toBeLessThanOrEqual(panel.x + panel.width + 0.5);
    expect(box.y + box.height).toBeLessThanOrEqual(panel.y + panel.height + 0.5);

    // delete: confirmation, cancel keeps it, confirm removes it everywhere
    await page.getByRole("menuitem", { name: "Löschen" }).click();
    const dialog = page.getByTestId("global-chat-delete-dialog");
    await expect(dialog).toBeVisible();
    await dialog.getByRole("button", { name: "Abbrechen" }).click();
    await expect(dialog).toHaveCount(0);
    await expect(edited).toBeVisible();
    await edited.getByTestId("global-chat-message-menu").click();
    await page.getByRole("menuitem", { name: "Löschen" }).click();
    await page.getByTestId("global-chat-delete-confirm").click();
    await expect(page.getByTestId("global-chat-message").filter({ hasText: fixed })).toHaveCount(0);
    await expect(readerPage.getByTestId("global-chat-message").filter({ hasText: fixed })).toHaveCount(0, { timeout: 10_000 });
    await reader.close();
  });

  test("the chat window stays inside the screen", async ({ page }) => {
    await useLanguage(page, "de");
    await loginViaForm(page, STUDENT2, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);    const viewport = page.viewportSize()!;
    const button = await page.getByTestId("global-chat-button").boundingBox();
    expect(button).not.toBeNull();
    expect(button!.x + button!.width).toBeLessThanOrEqual(viewport.width);
    expect(button!.y + button!.height).toBeLessThanOrEqual(viewport.height);

    await openChat(page);
    const panel = (await page.getByTestId("global-chat-panel").boundingBox())!;
    expect(panel.x).toBeGreaterThanOrEqual(0);
    expect(panel.y).toBeGreaterThanOrEqual(0);
    expect(panel.x + panel.width).toBeLessThanOrEqual(viewport.width + 0.5);
    expect(panel.y + panel.height).toBeLessThanOrEqual(viewport.height + 0.5);
    const input = (await page.getByTestId("global-chat-input").boundingBox())!;
    expect(input.y + input.height).toBeLessThanOrEqual(viewport.height);
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    expect(scrollWidth).toBeLessThanOrEqual(viewport.width);
    await expect(page.getByTestId("global-chat-panel")).toContainText("Global Chat");
    await page.keyboard.press("Escape");
    await expect(page.getByTestId("global-chat-panel")).toHaveCount(0);
  });
});
