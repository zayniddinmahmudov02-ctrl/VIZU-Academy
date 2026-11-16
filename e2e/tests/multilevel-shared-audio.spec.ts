import { expect, test, type Page } from "@playwright/test";

import { ADMIN, API_URL, PASSWORD, createStudent, loginViaForm, useLanguage } from "./helpers";

// Multilevel Modelltest 1: ONE shared Hören audio for all Teile. Admin: one upload / replacement for the whole Hören section (Multilevel Audio page); student:
// one player that keeps playing while the Teile are answered, six Teile with their own questions, the exam time independent of the audio length.
// Local stack only (needs ffmpeg: FFMPEG_BIN for the backend). The audio files are generated sine WAVs — test data. The run ends with Modelltest 1 published
// and playing a shared audio (multilevel-exam.spec.ts needs it published).

function wav(seconds: number): Buffer {
  const rate = 22050;
  const n = rate * seconds;
  const data = Buffer.alloc(n * 2);
  for (let i = 0; i < n; i += 1) data.writeInt16LE(Math.round(12000 * Math.sin((2 * Math.PI * 330 * i) / rate)), i * 2);
  const head = Buffer.alloc(44);
  head.write("RIFF", 0); head.writeUInt32LE(36 + data.length, 4); head.write("WAVEfmt ", 8);
  head.writeUInt32LE(16, 16); head.writeUInt16LE(1, 20); head.writeUInt16LE(1, 22); head.writeUInt32LE(rate, 24);
  head.writeUInt32LE(rate * 2, 28); head.writeUInt16LE(2, 32); head.writeUInt16LE(16, 34); head.write("data", 36); head.writeUInt32LE(data.length, 40);
  return Buffer.concat([head, data]);
}
const file = (name: string, seconds: number) => ({ name, mimeType: "audio/wav", buffer: wav(seconds) });

// the exam page starts the audio by script (headless Chromium may autoplay); a real student presses play
test.use({ launchOptions: { args: ["--autoplay-policy=no-user-gesture-required"] } });

async function adminToken() {
  const login = await fetch(`${API_URL}/api/v1/auth/login`, { method: "POST", headers: { "Content-Type": "application/json", "X-Forwarded-For": `10.93.${Math.floor(Math.random() * 250)}.${Math.floor(Math.random() * 250)}` }, body: JSON.stringify({ identifier: ADMIN.email, password: ADMIN.password }) });
  expect(login.status).toBe(200);
  return (await login.json()).access_token as string;
}
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Json = any;
async function call(method: string, url: string, bearer: string | null, body?: unknown): Promise<{ status: number; json: Json }> {
  const res = await fetch(`${API_URL}/api/v1${url}`, { method, headers: { ...(bearer ? { Authorization: `Bearer ${bearer}` } : {}), ...(body ? { "Content-Type": "application/json" } : {}) }, body: body ? JSON.stringify(body) : undefined });
  const text = await res.text();
  return { status: res.status, json: text && res.headers.get("content-type")?.includes("json") ? JSON.parse(text) : null };
}
async function adminLogin(page: Page) {
  await useLanguage(page, "de");
  await loginViaForm(page, ADMIN.email, ADMIN.password);
  await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
  await page.getByRole("button", { name: "Bestätigen" }).click();
  await expect(page).toHaveURL(/\/admin/);
}
async function noHorizontalScroll(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
}
async function mt1(token: string) {
  const overview = (await call("GET", "/admin/multilevel-audio", token)).json;
  return overview.tests.find((t: { sort_order: number }) => t.sort_order === 1) as { model_test_id: string; status: string; shared: Json; slots: Json[] };
}

test.describe.serial("Modelltest 1: one shared Hören audio", () => {
  let token = "";

  test.beforeAll(async () => {
    token = await adminToken();
  });

  test("security: the shared-audio routes are closed to anonymous users and students", async () => {
    const test1 = await mt1(token);
    const student = await createStudent();
    const bearer = (await (await fetch(`${API_URL}/api/v1/auth/login`, { method: "POST", headers: { "Content-Type": "application/json", "X-Forwarded-For": "10.93.9.9" }, body: JSON.stringify({ identifier: student, password: PASSWORD }) })).json()).access_token as string;
    const base = `/admin/multilevel-audio/shared/${test1.model_test_id}`;
    for (const [method, url, body] of [["GET", base, undefined], ["PUT", base, { audio_file_id: test1.model_test_id }], ["DELETE", base, undefined], ["GET", `${base}/file`, undefined]] as const) {
      expect((await call(method, url, null, body)).status, `anonymous ${method} ${url}`).toBe(401);
      expect((await call(method, url, bearer, body)).status, `student ${method} ${url}`).toBe(403);
    }
    expect((await fetch(`${API_URL}/api/v1/multilevel-exam/audio-shared/${test1.shared.kompetenz_id}`)).status).toBe(422); // a token is required
    expect((await fetch(`${API_URL}/api/v1/multilevel-exam/audio-shared/${test1.shared.kompetenz_id}?token=garbage`)).status).toBe(401);
    // another Modelltest has no shared audio
    const overview = (await call("GET", "/admin/multilevel-audio", token)).json;
    const other = overview.tests.find((t: { sort_order: number }) => t.sort_order === 2);
    expect(other.shared).toBeNull();
    expect((await call("GET", `/admin/multilevel-audio/shared/${other.model_test_id}`, token)).status).toBe(404);
  });

  test("admin: one upload for the whole Hören section of Modelltest 1, replace, per-Teil slots refused, other Modelltests unchanged", async ({ page, isMobile }) => {
    test.skip(isMobile, "the admin flow runs on desktop");
    await adminLogin(page);
    await page.goto("/admin/mock-exams/multilevel-audio");
    await expect(page.getByTestId("multilevel-audio")).toBeVisible();
    const card = page.locator("div", { has: page.getByRole("heading", { name: "Modelltest 1", exact: true }) }).filter({ has: page.getByTestId("ml-shared") }).last();
    const shared = page.getByTestId("ml-shared");
    await expect(shared).toHaveCount(1); // only Modelltest 1 has a shared audio slot
    await expect(shared.getByTestId("ml-shared-teile").getByTestId("ml-audio-slot")).toHaveCount(6); // all six Hören Teile are listed under it …
    await expect(shared.getByTestId("ml-shared-teile")).toContainText("nutzt das gemeinsame Audio");
    await expect(card.getByTestId("ml-audio-upload")).toHaveCount(0); // … and none of them has an upload button of its own
    await expect(page.getByTestId("ml-audio-upload").first()).toBeVisible(); // the other Modelltests keep one slot per Teil
    await expect(shared.getByTestId("ml-shared-minutes")).toContainText("Prüfungszeit Hören: 60 Min. (unabhängig von der Audiolänge)");

    // upload one 40 s audio, used as it is
    const [chooser] = await Promise.all([page.waitForEvent("filechooser"), shared.getByTestId("ml-shared-upload").click()]);
    await chooser.setFiles(file("modelltest1-hoeren.wav", 40));
    await expect(page.getByTestId("audio-trimmer")).toBeVisible();
    await expect(page.getByTestId("trim-original-status")).toContainText("Original gespeichert", { timeout: 30_000 });
    await expect(page.getByTestId("trim-end")).not.toHaveValue("00:00.0");
    await page.getByTestId("trim-use-original").click();
    await expect(page.getByTestId("audio-trimmer")).toHaveCount(0, { timeout: 30_000 });
    await expect(page.getByTestId("ml-audio-msg")).toContainText("alle Hören-Teile spielen es jetzt ab");
    await expect(shared).toHaveAttribute("data-status", "ok");
    await expect(shared.getByTestId("ml-shared-meta")).toContainText("Audiolänge 00:40");
    await expect(shared.getByTestId("ml-shared-minutes")).toContainText("60 Min."); // the exam time did not follow the 40 s
    await shared.getByTestId("ml-shared-play").click();
    await expect(shared.getByTestId("ml-shared-player")).toBeVisible();

    // replace it by a longer file: the section plays the new one, the exam time is still its own setting
    const [chooser2] = await Promise.all([page.waitForEvent("filechooser"), shared.getByTestId("ml-shared-upload").click()]);
    await chooser2.setFiles(file("modelltest1-hoeren-neu.wav", 45));
    await expect(page.getByTestId("trim-original-status")).toContainText("Original gespeichert", { timeout: 30_000 });
    await expect(page.getByTestId("trim-end")).not.toHaveValue("00:00.0");
    await page.getByTestId("trim-use-original").click();
    await expect(page.getByTestId("audio-trimmer")).toHaveCount(0, { timeout: 30_000 });
    await expect(shared.getByTestId("ml-shared-meta")).toContainText("Audiolänge 00:45");

    // the API agrees: one audio for the section; a Teil of this test refuses an audio of its own (409), a Teil of Modelltest 2 still takes one
    const test1 = await mt1(token);
    expect(test1.shared.status).toBe("ok");
    expect(test1.slots.every((s: { shared: boolean; status: string }) => s.shared && s.status === "ok")).toBe(true);
    const attach = await call("PUT", `/admin/multilevel-audio/slots/${test1.slots[0].content_id}`, token, { audio_file_id: test1.shared.audio.id });
    expect(attach.status).toBe(409);
    expect(String(attach.json.message)).toContain("SHARED_AUDIO_TEST");
    expect((await call("DELETE", `/admin/multilevel-audio/slots/${test1.slots[0].content_id}`, token)).status).toBe(409);
    // the Modelltest is ready as far as the audio is concerned and stays published
    expect(test1.status).toBe("PUBLISHED");
    const keys = (await call("GET", `/admin/multilevel-exam/model-tests/${test1.model_test_id}/answer-keys?section=HOEREN`, token)).json;
    expect(keys.readiness.missing_audio).toEqual([]);
    await page.screenshot({ path: "test-results/multilevel-shared-audio-admin.png", fullPage: true });
  });

  test("student: one player for all six Teile, it keeps playing while the Teile are answered, a reload continues near the same place", async ({ page, isMobile }) => {
    test.setTimeout(120_000);
    await useLanguage(page, "de");
    const email = await createStudent();
    await loginViaForm(page, email, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);
    await page.goto("/vorbereitung/multilevel");
    await page.getByTestId("multilevel-exam-1").getByTestId("start-exam").click();
    await expect(page.getByTestId("exam-overview")).toBeVisible();
    const attemptId = page.url().split("/").pop()!;
    await page.getByTestId("exam-section-HOEREN").getByRole("button", { name: "Teil starten" }).click();
    await expect(page.getByTestId("exam-section")).toBeVisible();

    // ONE audio element for the whole section, six Teile each with its own questions (35)
    await expect(page.getByTestId("shared-audio")).toHaveCount(1);
    expect(await page.getByTestId("exam-section").locator("audio").count()).toBe(1); // (the dashboard's own music player lives outside the exam)
    await expect(page.getByTestId("paper-teil")).toHaveCount(6);
    await expect(page.getByTestId("teil-shared-audio-note")).toHaveCount(6);
    await expect(page.getByTestId("exam-question")).toHaveCount(35);
    await expect(page.getByRole("heading", { name: /^Teil [1-6]$/ })).toHaveCount(6); // Teil 1 … Teil 6, each shown on its own
    await expect(page.getByTestId("shared-audio-length")).toContainText("0:45");
    await expect(page.getByTestId("exam-timer")).toHaveText(/^(60:00|59:5\d)$/); // the 60 minute section timer next to a 45 second audio
    expect(await page.content()).not.toContain("is_correct");
    await noHorizontalScroll(page);
    const audioBox = await page.getByTestId("shared-audio-box").boundingBox();
    expect(audioBox!.width).toBeLessThanOrEqual(page.viewportSize()!.width);
    if (isMobile) await page.screenshot({ path: "test-results/multilevel-shared-audio-mobile.png" });

    // play, then work through the Teile: the same element keeps playing — no restart when another Teil is on screen
    const src = await page.getByTestId("shared-audio").getAttribute("src");
    expect(src).toMatch(/\/api\/v1\/multilevel-exam\/audio-shared\/.+\?token=/);
    await page.evaluate(() => { const a = document.querySelector('[data-testid="shared-audio"]') as HTMLAudioElement; (window as unknown as { __audio: Element }).__audio = a; return a.play(); });
    await expect.poll(() => page.evaluate(() => (document.querySelector('[data-testid="shared-audio"]') as HTMLAudioElement).currentTime), { timeout: 20_000 }).toBeGreaterThan(1.5);
    const before = await page.evaluate(() => (document.querySelector('[data-testid="shared-audio"]') as HTMLAudioElement).currentTime);
    for (const index of [1, 3, 5]) {
      const teil = page.getByTestId("paper-teil").nth(index);
      await teil.scrollIntoViewIfNeeded();
      await teil.getByTestId("exam-question").first().getByTestId("exam-option").nth(0).click(); // answer in this Teil
      await expect(teil.getByTestId("exam-question").first().getByText("Gespeichert")).toBeVisible({ timeout: 10_000 });
    }
    const after = await page.evaluate(() => {
      const a = document.querySelector('[data-testid="shared-audio"]') as HTMLAudioElement;
      return { t: a.currentTime, paused: a.paused, ended: a.ended, same: (window as unknown as { __audio: Element }).__audio === a, duration: a.duration,
               count: document.querySelectorAll('[data-testid="exam-section"] audio').length };
    });
    expect(after.same).toBe(true); // the very same element (no remount)
    expect(after.count).toBe(1);
    expect(after.paused).toBe(false);
    expect(after.ended).toBe(false);
    expect(after.t).toBeGreaterThan(before); // it went on, it did not start over
    expect(after.duration).toBeGreaterThan(44);
    await expect(page.getByTestId("shared-audio-box")).toBeInViewport(); // the docked player stays on screen while the last Teil is answered
    await page.screenshot({ path: `test-results/multilevel-shared-audio-${isMobile ? "mobile" : "desktop"}-teil6.png` });

    // reload: the section continues (timer from the server) and the audio is positioned near where it was
    await page.evaluate(() => (document.querySelector('[data-testid="shared-audio"]') as HTMLAudioElement).pause());
    const at = await page.evaluate(() => (document.querySelector('[data-testid="shared-audio"]') as HTMLAudioElement).currentTime);
    await page.waitForTimeout(500);
    await page.reload();
    await page.getByTestId("exam-section-HOEREN").getByRole("button", { name: "Weiter" }).click();
    await expect(page.getByTestId("shared-audio")).toHaveCount(1);
    await expect.poll(() => page.evaluate(() => (document.querySelector('[data-testid="shared-audio"]') as HTMLAudioElement).currentTime), { timeout: 15_000 }).toBeGreaterThan(Math.max(0.5, at - 3));
    const restored = await page.evaluate(() => (document.querySelector('[data-testid="shared-audio"]') as HTMLAudioElement).currentTime);
    expect(restored).toBeLessThan(at + 3);
    // the answers are still there (saved by the server) and the timer is not reset
    await expect(page.getByTestId("exam-question").nth(5).getByTestId("exam-option").nth(0)).toBeVisible();
    const view = (await call("GET", `/multilevel-exam/attempts/${attemptId}`, await studentToken(email))).json;
    const hoeren = view.sections.find((s: { type: string }) => s.type === "HOEREN");
    expect(hoeren.duration_seconds).toBe(3600);
    expect(hoeren.remaining_seconds).toBeLessThan(3600);
    expect(hoeren.remaining_seconds).toBeGreaterThan(3400);
    await noHorizontalScroll(page);
  });

  test("admin preview of Modelltest 1 shows the same single audio", async ({ page, isMobile }) => {
    test.skip(isMobile, "the admin flow runs on desktop");
    await adminLogin(page);
    await page.goto("/admin/mock-exams/multilevel");
    await page.getByRole("link", { name: "Vorschau" }).first().click();
    await page.getByRole("button", { name: /Hören · \d+ Min\./ }).click();
    await expect(page.getByTestId("shared-audio")).toHaveCount(1);
    expect(await page.locator("main audio").count()).toBe(1);
    await expect(page.getByTestId("teil-shared-audio-note").first()).toBeVisible();
  });
});

async function studentToken(email: string): Promise<string> {
  const res = await fetch(`${API_URL}/api/v1/auth/login`, { method: "POST", headers: { "Content-Type": "application/json", "X-Forwarded-For": `10.93.${Math.floor(Math.random() * 250)}.${Math.floor(Math.random() * 250)}` }, body: JSON.stringify({ identifier: email, password: PASSWORD }) });
  expect(res.status).toBe(200);
  return (await res.json()).access_token as string;
}
