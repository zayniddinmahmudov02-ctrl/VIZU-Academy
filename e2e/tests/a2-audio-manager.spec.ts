import { expect, test, type Page } from "@playwright/test";

import { ADMIN, API_URL, loginViaForm, useLanguage } from "./helpers";

// A2 Audio Manager against the throwaway stack. The seed (D:\vz_tmp\work\gcr_e2e_seed.py, DB vizu_gcr_e2e) publishes
// A2 lessons 1 and 2, each with one Hören task "E2E Hören Lektion N" without audio,
// and keeps A2 sales closed (the code default). The audio files here are tiny
// generated MP3 / M4A headers — test data, not course audio.
const STUDENT = "gc-student1@example.com";
const PASSWORD = "Geheim123!";

const mp3 = (seed: string) => Buffer.concat([Buffer.from("ID3\x04\x00\x00\x00\x00\x00\x00", "latin1"), Buffer.from(seed.repeat(200))]);
const m4a = (seed: string) => Buffer.concat([Buffer.from([0, 0, 0, 0x20]), Buffer.from("ftypM4A \x00\x00\x00\x00", "latin1"), Buffer.from(seed.repeat(200))]);

async function token(identifier: string, password: string) {
  const res = await fetch(`${API_URL}/api/v1/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ identifier, password }) });
  expect(res.status).toBe(200);
  return (await res.json()).access_token as string;
}

async function adminLogin(page: Page) {
  await useLanguage(page, "de");
  await loginViaForm(page, ADMIN.email, ADMIN.password);
  await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
  await page.getByRole("button", { name: "Bestätigen" }).click();
  await expect(page).toHaveURL(/\/admin/);
}

async function a2Lessons(adminToken: string) {
  const res = await fetch(`${API_URL}/api/v1/admin/media-management/a2-audio/targets`, { headers: { Authorization: `Bearer ${adminToken}` } });
  expect(res.status).toBe(200);
  return (await res.json()) as { listening_id: string; lesson_number: number; title: string }[];
}

test.describe.serial("A2 Audio Manager", () => {
  test.skip(({ isMobile }) => isMobile, "admin flow runs on desktop; the student check below runs on both");

  test("students and anonymous users can not use the A2 library", async () => {
    expect((await fetch(`${API_URL}/api/v1/admin/media-management/a2-audio/assets`)).status).toBe(401);
    const student = await token(STUDENT, PASSWORD);
    const auth = { Authorization: `Bearer ${student}` };
    expect((await fetch(`${API_URL}/api/v1/admin/media-management/a2-audio/assets`, { headers: auth })).status).toBe(403);
    expect((await fetch(`${API_URL}/api/v1/admin/media-management/a2-readiness`, { headers: auth })).status).toBe(403);
  });

  test("admin: batch upload with import report, duplicate, link, verify", async ({ page }) => {
    await adminLogin(page);
    await page.goto("/admin/media-management?level=A2");
    await expect(page.getByTestId("a2-audio-manager")).toBeVisible();
    const readiness = page.getByTestId("a2-readiness");
    await expect(readiness).toBeVisible();
    await expect(readiness).not.toHaveAttribute("data-status", "READY"); // no real audio yet

    const seed = String(Date.now());
    await page.getByTestId("a2-import-input").setInputFiles([
      { name: "A2 1.Unterricht Hören.mp3", mimeType: "audio/mpeg", buffer: mp3(`a${seed}`) },
      { name: "A2 2.Unterricht Hören.m4a", mimeType: "audio/mp4", buffer: m4a(`b${seed}`) },
      { name: "A2 3.Unterricht Hören.wav", mimeType: "audio/wav", buffer: Buffer.from("RIFF0000WAVEfmt ") },
      { name: "A2 4.Unterricht Text 1.mp3", mimeType: "audio/mpeg", buffer: m4a(`c${seed}`) }, // content is M4A
    ]);
    const summary = page.getByTestId("a2-import-summary");
    await expect(summary).toContainText("4/4 verarbeitet", { timeout: 30_000 });
    await expect(summary).toContainText("2 erfolgreich");
    await expect(summary).toContainText("2 Fehler");
    await expect(page.getByTestId("a2-import-row").filter({ hasText: ".wav" })).toContainText("MP3 oder M4A");
    await expect(page.getByTestId("a2-import-row").filter({ hasText: "Text 1" })).toContainText("EXTENSION_MISMATCH");

    // the same content again, under another name -> duplicate, nothing new in the library
    await page.getByTestId("a2-import-input").setInputFiles([{ name: "kopie.mp3", mimeType: "audio/mpeg", buffer: mp3(`a${seed}`) }]);
    await expect(summary).toContainText("1 Duplikat", { timeout: 15_000 });
    await expect(page.getByTestId("a2-import-row")).toContainText("A2 1.Unterricht Hören.mp3");

    // parsed into the right Unterricht, suggested but not linked
    const asset = page.getByTestId("a2-group-1").getByTestId("a2-asset").first();
    await expect(asset).toContainText("Original: A2 1.Unterricht Hören.mp3");
    await expect(asset).toContainText("Vorschlag");
    await expect(asset).toContainText("E2E Hören Lektion 1");
    await asset.getByRole("button", { name: "Geprüft" }).click();
    await expect(page.getByTestId("a2-group-1").getByTestId("a2-asset").first()).toContainText("geprüft");
    const row = page.getByTestId("a2-group-1").getByTestId("a2-asset").first();
    await row.getByTestId("a2-link").click();
    await expect(row.getByTestId("a2-link-target")).not.toHaveValue(""); // the suggestion is preselected, not applied
    await row.getByRole("button", { name: "Verknüpfung bestätigen" }).click();
    await expect(page.getByTestId("a2-group-1").getByTestId("a2-asset").first()).toContainText("Verknüpft mit 1. Unterricht · E2E Hören Lektion 1");
    await expect(page.getByTestId("a2-manifest-counts")).toContainText("1 verknüpft");
  });

  test("student: the linked audio plays in lesson 1 after publishing; lesson 2 stays closed", async ({ page, browser }) => {
    const admin = await token(ADMIN.email, ADMIN.password);
    const tasks = await a2Lessons(admin);
    const t1 = tasks.find((t) => t.lesson_number === 1)!;
    const t2 = tasks.find((t) => t.lesson_number === 2)!;
    // linking left the task as a draft: the admin publishes after checking
    const pub = await fetch(`${API_URL}/api/v1/listenings/${t1.listening_id}`, {
      method: "PUT", headers: { "Content-Type": "application/json", Authorization: `Bearer ${admin}` }, body: JSON.stringify({ is_published: true }),
    });
    expect(pub.status, await pub.clone().text()).toBe(200);

    const student = await token(STUDENT, PASSWORD);
    const lessons = await (await fetch(`${API_URL}/api/v1/admin/media-management/a2-audio/manifest`, { headers: { Authorization: `Bearer ${admin}` } })).json();
    expect(lessons.counts.linked).toBeGreaterThanOrEqual(1);
    const tree = await (await fetch(`${API_URL}/api/v1/admin/media-management/tree`, { headers: { Authorization: `Bearer ${admin}` } })).json();
    const a2 = tree.find((l: { level: string }) => l.level === "A2");
    const lesson1 = a2.modules[0].lessons.find((l: { number: number }) => l.number === 1).id;
    const lesson2 = a2.modules[0].lessons.find((l: { number: number }) => l.number === 2).id;
    const auth = { Authorization: `Bearer ${student}` };
    const ok = await fetch(`${API_URL}/api/v1/lesson-skills/${lesson1}/hoeren/${t1.listening_id}/audio`, { headers: auth });
    expect(ok.status).toBe(200);
    expect(ok.headers.get("cache-control")).toBe("private, no-store");
    expect((await fetch(`${API_URL}/api/v1/lesson-skills/${lesson1}/hoeren/${t1.listening_id}/audio`)).status).toBe(401);
    expect((await fetch(`${API_URL}/api/v1/lesson-skills/${lesson2}/hoeren/${t2.listening_id}/audio`, { headers: auth })).status).toBe(403);
    // A2 is not for sale yet: the price shown is the backend's, the checkout refuses
    const offers = await (await fetch(`${API_URL}/api/v1/vizu-pay/offers`, { headers: auth })).json();
    const a2offer = (Array.isArray(offers) ? offers : offers.offers).find((o: { code: string }) => o.code === "A2");
    expect(a2offer).toMatchObject({ sale_price: 99000, purchasable: false });

    const context = await browser.newContext();
    const studentPage = await context.newPage();
    await useLanguage(studentPage, "de");
    await loginViaForm(studentPage, STUDENT, PASSWORD);
    await expect(studentPage).toHaveURL(/\/dashboard/);
    await studentPage.goto(`/lektion/${lesson1}/hoeren`);
    await expect(studentPage.getByTestId("hoeren-task")).toContainText("E2E Hören Lektion 1", { timeout: 20_000 });
    await expect(studentPage.getByTestId("hoeren-task").locator("audio")).toHaveCount(1);
    await context.close();
    void page;
  });
});
