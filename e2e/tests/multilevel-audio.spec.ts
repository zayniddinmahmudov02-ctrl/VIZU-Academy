import { expect, test, type Page } from "@playwright/test";

import { ADMIN, API_URL, loginViaForm, useLanguage } from "./helpers";

// Media Management audio upload + trim, and the Multilevel Audio page (Vorbereitung): upload, trim, replace, delete per
// Hören Teil, and the audio playing in the Multilevel Modelltest. Local stack only (needs ffmpeg: FFMPEG_BIN for the
// backend). The audio files are generated sine WAVs — test data. Destructive steps use Modelltest 2 (a draft); Modelltest 1
// stays published for multilevel-exam.spec.ts.

function wav(seconds: number): Buffer {
  const rate = 22050;
  const n = rate * seconds;
  const data = Buffer.alloc(n * 2);
  for (let i = 0; i < n; i += 1) data.writeInt16LE(Math.round(12000 * Math.sin((2 * Math.PI * 440 * i) / rate)), i * 2);
  const head = Buffer.alloc(44);
  head.write("RIFF", 0); head.writeUInt32LE(36 + data.length, 4); head.write("WAVEfmt ", 8);
  head.writeUInt32LE(16, 16); head.writeUInt16LE(1, 20); head.writeUInt16LE(1, 22); head.writeUInt32LE(rate, 24);
  head.writeUInt32LE(rate * 2, 28); head.writeUInt16LE(2, 32); head.writeUInt16LE(16, 34); head.write("data", 36); head.writeUInt32LE(data.length, 40);
  return Buffer.concat([head, data]);
}
const file = (name: string, seconds: number) => ({ name, mimeType: "audio/wav", buffer: wav(seconds) });

async function adminLogin(page: Page) {
  await useLanguage(page, "de");
  await loginViaForm(page, ADMIN.email, ADMIN.password);
  await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
  await page.getByRole("button", { name: "Bestätigen" }).click();
  await expect(page).toHaveURL(/\/admin/);
}

async function adminToken() {
  const login = await fetch(`${API_URL}/api/v1/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ identifier: ADMIN.email, password: ADMIN.password }) });
  expect(login.status).toBe(200);
  return (await login.json()).access_token as string; // the admin password prompt is a UI gate; the API checks the role
}

type Slot = { content_id: string; aufgabe_number: number; status: string; duration_ms: number | null; audio: { kind: string } | null; original: { id: string } | null };
type Overview = { total: number; tests: { model_test_id: string; title: string; status: string; slots: Slot[] }[] };

async function overview(token: string): Promise<Overview> {
  const res = await fetch(`${API_URL}/api/v1/admin/multilevel-audio`, { headers: { Authorization: `Bearer ${token}` } });
  expect(res.status).toBe(200);
  return res.json();
}

async function noHorizontalScroll(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
}

/** open the slot's file chooser, pick the file and wait until the trimmer knows its duration */
async function pickInto(page: Page, buttonTestId: string, slotLocator: ReturnType<Page["locator"]>, f: ReturnType<typeof file>) {
  const [chooser] = await Promise.all([page.waitForEvent("filechooser"), slotLocator.getByTestId(buttonTestId).click()]);
  await chooser.setFiles(f);
  await expect(page.getByTestId("audio-trimmer")).toBeVisible();
  await expect(page.getByTestId("trim-original-status")).toContainText("Original gespeichert", { timeout: 30_000 });
  await expect(page.getByTestId("trim-end")).not.toHaveValue("00:00.0");
}

test.describe.serial("Multilevel Audio + trim", () => {
  test("anonymous and student cannot use the audio endpoints", async () => {
    expect((await fetch(`${API_URL}/api/v1/admin/multilevel-audio`)).status).toBe(401);
    expect((await fetch(`${API_URL}/api/v1/admin/audio-files`, { method: "POST" })).status).toBe(401);
    expect((await fetch(`${API_URL}/api/v1/multilevel-exam/audio/00000000-0000-0000-0000-000000000000?token=x`)).status).toBe(401);
  });

  test("Media Management: upload, trim to 4.5 s, original kept (desktop)", async ({ page, isMobile }) => {
    test.skip(isMobile, "admin flow runs on desktop");
    await adminLogin(page);
    await page.goto("/admin/media-management?level=A1");
    const row = page.getByTestId("mm-row").filter({ has: page.locator('[data-testid="mm-slots"]') }).first();
    await expect(row).toBeVisible({ timeout: 20_000 });
    await row.getByTestId("mm-slots").click();
    const slot = page.getByTestId("mm-slots-row").first().getByTestId("audio-slot").first();
    await pickInto(page, "audio-slot-trim", slot, file("e2e-trim-source.wav", 10));
    await expect(page.getByTestId("trim-original-status")).toContainText("bleibt immer erhalten");
    await page.getByTestId("trim-start").fill("2");
    await page.getByTestId("trim-start").blur();
    await page.getByTestId("trim-end").fill("0:06,5");
    await page.getByTestId("trim-end").blur();
    await expect(page.getByTestId("trim-length")).toHaveText("00:04.5");
    await page.getByTestId("trim-preview").click();
    await page.screenshot({ path: "test-results/audio-trimmer-desktop.png" });
    await page.getByTestId("trim-save").click();
    await expect(page.getByTestId("trim-result-player")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId("trim-result")).toContainText("00:04.");
    await page.getByTestId("trim-apply").click();
    await expect(page.getByTestId("audio-trimmer")).toHaveCount(0, { timeout: 30_000 });
    await expect(slot).toHaveAttribute("data-file", "ok", { timeout: 20_000 });
    // clean up: remove the file again (the slot stays)
    await slot.getByTestId("audio-slot-delete").click();
    await page.getByRole("button", { name: /Entfernen|Löschen|Bestätigen/ }).last().click();
    await expect(slot).toHaveAttribute("data-file", "none", { timeout: 20_000 });
  });

  test("Multilevel Audio: every slot listed, upload / trim / replace / delete (desktop)", async ({ page, isMobile }) => {
    test.skip(isMobile, "admin flow runs on desktop; mobile layout is checked below");
    const token = await adminToken();
    const before = await overview(token);
    const all = before.tests.flatMap((t) => t.slots);
    const draft = before.tests.find((t) => t.status === "DRAFT" && t.slots.length >= 2)!;
    expect(draft, "a draft Modelltest with at least two Hören Teile").toBeTruthy();

    await adminLogin(page);
    await page.goto("/admin/mock-exams/multilevel-audio");
    await expect(page.getByTestId("multilevel-audio")).toBeVisible();
    await expect(page.getByTestId("ml-audio-slot")).toHaveCount(all.length); // every Hören Teil of every Modelltest has its slot
    await expect(page.getByTestId("ml-audio-summary")).toContainText(`/ ${all.length} Aufgaben`);
    await expect(page.getByRole("link", { name: "Multilevel Audio" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Multilevel Modelltest" })).toBeVisible();

    const s1 = page.locator(`[data-slot="${draft.slots[0].content_id}"]`);
    const s2 = page.locator(`[data-slot="${draft.slots[1].content_id}"]`);

    // Aufgabe 1: upload 10 s, trim 1.0–4.0 s
    await pickInto(page, "ml-audio-upload", s1, file("a1-aufgabe1.wav", 10));
    await page.getByTestId("trim-start").fill("1");
    await page.getByTestId("trim-start").blur();
    await page.getByTestId("trim-end").fill("4");
    await page.getByTestId("trim-end").blur();
    await page.getByTestId("trim-save").click();
    await expect(page.getByTestId("trim-result-player")).toBeVisible({ timeout: 30_000 });
    await page.getByTestId("trim-apply").click();
    await expect(page.getByTestId("audio-trimmer")).toHaveCount(0, { timeout: 30_000 });
    await expect(s1).toHaveAttribute("data-status", "ok");
    await expect(s1.getByTestId("ml-audio-meta")).toContainText("00:03.");
    await expect(s1.getByTestId("ml-audio-meta")).toContainText("gekürzt");

    // Aufgabe 2: upload and use the original uncut
    await pickInto(page, "ml-audio-upload", s2, file("a1-aufgabe2.wav", 6));
    await page.getByTestId("trim-use-original").click();
    await expect(page.getByTestId("audio-trimmer")).toHaveCount(0, { timeout: 30_000 });
    await expect(s2).toHaveAttribute("data-status", "ok");
    await expect(s2.getByTestId("ml-audio-meta")).toContainText("00:06.");

    // listen
    await s1.getByTestId("ml-audio-play").click();
    await expect(s1.getByTestId("ml-audio-player")).toBeVisible();

    // the original is kept and a re-trim cuts from it (0–2 s)
    const afterTrim = await overview(token);
    const slot1 = afterTrim.tests.flatMap((t) => t.slots).find((s) => s.content_id === draft.slots[0].content_id)!;
    expect(slot1.audio?.kind).toBe("TRIMMED");
    expect(slot1.original).not.toBeNull();
    await s1.getByTestId("ml-audio-trim").click();
    await expect(page.getByTestId("audio-trimmer")).toBeVisible();
    await expect(page.getByTestId("trim-original-status")).toContainText("Original gespeichert");
    await expect(page.getByTestId("trim-end")).not.toHaveValue("00:00.0", { timeout: 20_000 });
    await page.getByTestId("trim-end").fill("2");
    await page.getByTestId("trim-end").blur();
    await page.getByTestId("trim-save").click();
    await expect(page.getByTestId("trim-result-player")).toBeVisible({ timeout: 30_000 });
    await page.getByTestId("trim-apply").click();
    await expect(page.getByTestId("audio-trimmer")).toHaveCount(0, { timeout: 30_000 });
    await expect(s1.getByTestId("ml-audio-meta")).toContainText("00:02.");

    // replace Aufgabe 2 with a new file (3 s)
    await pickInto(page, "ml-audio-upload", s2, file("a1-aufgabe2-neu.wav", 3));
    await page.getByTestId("trim-use-original").click();
    await expect(page.getByTestId("audio-trimmer")).toHaveCount(0, { timeout: 30_000 });
    await expect(s2.getByTestId("ml-audio-meta")).toContainText("00:03.");

    // the audio plays in the Modelltest: the exam paper (admin preview) points at it and the stream answers with the file
    const preview = await (await fetch(`${API_URL}/api/v1/admin/multilevel-exam/model-tests/${draft.model_test_id}/preview`, { headers: { Authorization: `Bearer ${token}` } })).json();
    const hoeren = preview.sections.find((s: { type: string }) => s.type === "HOEREN");
    const urls: (string | null)[] = hoeren.teile.map((t: { audio_url: string | null }) => t.audio_url);
    expect(urls[0]).toMatch(/^\/api\/v1\/multilevel-exam\/audio\//);
    const stream = await fetch(`${API_URL}${urls[0]}`);
    expect(stream.status).toBe(200);
    expect(stream.headers.get("content-type")).toContain("audio/");
    expect((await stream.arrayBuffer()).byteLength).toBeGreaterThan(1000);

    // delete Aufgabe 2: no audio any more, the preview shows no audio for that Teil (no error)
    await s2.getByTestId("ml-audio-delete").click();
    await page.getByRole("button", { name: /Löschen|Entfernen|Bestätigen/ }).last().click();
    await expect(s2).toHaveAttribute("data-status", "missing", { timeout: 20_000 });
    await expect(page.getByTestId("ml-audio-msg")).toContainText("Audio entfernt");
    const afterDelete = await (await fetch(`${API_URL}/api/v1/admin/multilevel-exam/model-tests/${draft.model_test_id}/preview`, { headers: { Authorization: `Bearer ${token}` } })).json();
    const teile = afterDelete.sections.find((s: { type: string }) => s.type === "HOEREN").teile;
    expect(teile[1].audio_url).toBeNull();
    expect(teile[0].audio_url).toMatch(/^\/api\/v1\/multilevel-exam\/audio\//);
    await page.screenshot({ path: "test-results/multilevel-audio-desktop.png", fullPage: true });

    // clean up Aufgabe 1 as well
    await s1.getByTestId("ml-audio-delete").click();
    await page.getByRole("button", { name: /Löschen|Entfernen|Bestätigen/ }).last().click();
    await expect(s1).toHaveAttribute("data-status", "missing", { timeout: 20_000 });
  });

  test("Multilevel Audio: a slot of another level can not be addressed", async () => {
    const token = await adminToken();
    const res = await fetch(`${API_URL}/api/v1/admin/multilevel-audio/slots/00000000-0000-0000-0000-000000000000`, { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBe(404);
  });

  test("mobile: Multilevel Audio page and trimmer fit the phone", async ({ page, isMobile }) => {
    test.skip(!isMobile, "phone layout");
    await adminLogin(page);
    await page.goto("/admin/mock-exams/multilevel-audio");
    await expect(page.getByTestId("multilevel-audio")).toBeVisible();
    await expect(page.getByTestId("ml-audio-slot").first()).toBeVisible();
    await noHorizontalScroll(page);
    const slot = page.getByTestId("ml-audio-slot").first();
    const [chooser] = await Promise.all([page.waitForEvent("filechooser"), slot.getByTestId("ml-audio-upload").click()]);
    await chooser.setFiles(file("mobile.wav", 4));
    await expect(page.getByTestId("audio-trimmer")).toBeVisible();
    await expect(page.getByTestId("trim-original-status")).toContainText("Original gespeichert", { timeout: 30_000 });
    await noHorizontalScroll(page);
    await expect(page.getByTestId("trim-save")).toBeVisible();
    await page.screenshot({ path: "test-results/audio-trimmer-mobile.png" });
    await page.getByTestId("trim-cancel").click();
    await expect(page.getByTestId("audio-trimmer")).toHaveCount(0);
  });
});
