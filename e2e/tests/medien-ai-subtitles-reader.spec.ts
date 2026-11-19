import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { expect, test, type Page } from "@playwright/test";

import { ADMIN, API_URL, PASSWORD, createStudent, loginViaForm } from "./helpers";

// VIZU MEDIENWELT: AI subtitles of a film (admin: generate from the audio with the LOCAL TEST provider — the local backend runs with
// SUBTITLE_STT_PROVIDER=fake, SUBTITLE_TRANSLATE_PROVIDER=fake, SUBTITLE_CHUNK_SECONDS=8; production uses Gemini), job status, draft → edit →
// approve, SRT download; student: original + translation at the same time, switched separately, in sync with the video), the Bibliothek
// bookshelf (one shelf per category, vertical, title / author / free / price + lock) and the book reader (keys, click zones, buttons,
// swipe, pinch zoom without turning the page, double tap, "close the book" → Bibliothek, resume, the preview paywall). Local stack only.
const FFMPEG = process.env.FFMPEG_BIN ?? "ffmpeg";
const TAG = `AI${Date.now().toString(36)}`;
const work = mkdtempSync(join(tmpdir(), "ai-subs-"));

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Json = any;
async function token(email: string, password: string) {
  const res = await fetch(`${API_URL}/api/v1/auth/login`, { method: "POST", headers: { "Content-Type": "application/json", "X-Forwarded-For": `10.97.${Math.floor(Math.random() * 250)}.${Math.floor(Math.random() * 250)}` }, body: JSON.stringify({ identifier: email, password }) });
  expect(res.status, await res.clone().text()).toBe(200);
  return (await res.json()).access_token as string;
}
const call = async (method: string, url: string, bearer: string, body?: unknown): Promise<{ status: number; json: Json }> => {
  const res = await fetch(`${API_URL}/api/v1${url}`, { method, headers: { Authorization: `Bearer ${bearer}`, ...(body ? { "Content-Type": "application/json" } : {}) }, body: body ? JSON.stringify(body) : undefined });
  const text = await res.text();
  return { status: res.status, json: text && res.headers.get("content-type")?.includes("json") ? JSON.parse(text) : null };
};
async function upload(url: string, bearer: string, file: Buffer, name: string, type: string) {
  const f = new FormData();
  f.append("file", new Blob([new Uint8Array(file)], { type }), name);
  const res = await fetch(`${API_URL}/api/v1${url}`, { method: "POST", headers: { Authorization: `Bearer ${bearer}` }, body: f });
  expect(res.status, await res.clone().text()).toBe(200);
  return res.json();
}

/** 20 s: a tone of 2.5 s every 4 s (speech with pauses) under a test picture — ffmpeg finds the pauses, the pieces are cut from it. */
function talkVideo(): Buffer {
  const p = join(work, "talk.mp4");
  execFileSync(FFMPEG, ["-nostdin", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=duration=20:size=320x180:rate=15", "-f", "lavfi",
    "-i", "aevalsrc='if(lt(mod(t,4),2.5),0.4*sin(2*PI*440*t),0)':s=16000:d=20", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", p], { stdio: "pipe" });
  return readFileSync(p);
}

/** A real PDF: page n carries the text "Seite n". */
function pdf(pages: number): Buffer {
  const objs: string[] = ["<</Type/Catalog/Pages 2 0 R>>", `<</Type/Pages/Kids[${Array.from({ length: pages }, (_, i) => `${3 + i * 2} 0 R`).join(" ")}]/Count ${pages}>>`];
  for (let i = 0; i < pages; i += 1) {
    const stream = `BT /F1 40 Tf 60 400 Td (Seite ${i + 1}) Tj ET`;
    objs.push(`<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 450]/Contents ${4 + i * 2} 0 R/Resources<</Font<</F1 ${3 + pages * 2} 0 R>>>>>>`, `<</Length ${stream.length}>>\nstream\n${stream}\nendstream`);
  }
  objs.push("<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>");
  let out = "%PDF-1.4\n";
  const offsets: number[] = [];
  objs.forEach((o, i) => { offsets.push(out.length); out += `${i + 1} 0 obj\n${o}\nendobj\n`; });
  const xref = out.length;
  out += `xref\n0 ${objs.length + 1}\n0000000000 65535 f \n${offsets.map((o) => `${String(o).padStart(10, "0")} 00000 n \n`).join("")}trailer\n<</Size ${objs.length + 1}/Root 1 0 R>>\nstartxref\n${xref}\n%%EOF\n`;
  return Buffer.from(out, "latin1");
}

async function adminLogin(page: Page) {
  await page.addInitScript(() => localStorage.setItem("vizu-language", JSON.stringify({ state: { language: "de" }, version: 0 })));
  await loginViaForm(page, ADMIN.email, ADMIN.password);
  await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
  await page.getByRole("button", { name: "Bestätigen" }).click();
  await expect(page).toHaveURL(/\/admin/);
}
async function studentLogin(page: Page, email: string, language = "de") {
  await loginViaForm(page, email, PASSWORD);
  await expect(page).toHaveURL(/\/dashboard/);
  await page.evaluate((l) => localStorage.setItem("vizu-language", JSON.stringify({ state: { language: l }, version: 0 })), language);
  await page.reload();
}
const noHorizontalScroll = async (page: Page) => expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);

/** Pointer events on the reader's page stage (x / y = share of its size). Several fingers = several pointer ids. */
async function gesture(page: Page, steps: { type: "pointerdown" | "pointermove" | "pointerup"; id: number; x: number; y: number }[], delay = 16) {
  await page.getByTestId("reader-book").evaluate(async (el, { steps: list, delay: wait }) => {
    const r = el.getBoundingClientRect();
    for (const s of list) {
      el.dispatchEvent(new PointerEvent(s.type, { pointerId: s.id, pointerType: "touch", isPrimary: s.id === 1, clientX: r.left + s.x * r.width, clientY: r.top + s.y * r.height,
        bubbles: true, cancelable: true, buttons: s.type === "pointerup" ? 0 : 1 }));
      await new Promise((res) => setTimeout(res, wait));
    }
  }, { steps, delay });
}
const swipe = (page: Page, from: number, to: number) => gesture(page, [
  { type: "pointerdown", id: 1, x: from, y: 0.5 }, ...[0.25, 0.5, 0.75, 1].map((k) => ({ type: "pointermove" as const, id: 1, x: from + (to - from) * k, y: 0.5 })),
  { type: "pointerup", id: 1, x: to, y: 0.5 }]);

// ---------------------------------------------------------------------------------------------------------------------------------------------------
test.describe.serial("AI subtitles: admin generates, reviews, approves — student sees original + translation", () => {
  test.skip(({ isMobile }) => isMobile, "desktop");
  let admin = "";
  let film = "";
  let student = "";

  test.beforeAll(async () => {
    admin = await token(ADMIN.email, ADMIN.password);
    student = await createStudent();
    film = (await call("POST", "/admin/medien/films", admin, { title: `${TAG} Sprechfilm`, level: "B1", status: "PUBLISHED", duration_minutes: 1, language: "de" })).json.id;
    await upload(`/admin/medien/films/${film}/video`, admin, talkVideo(), "talk.mp4", "video/mp4");
  });
  test.afterAll(async () => {
    if (film) await call("DELETE", `/admin/medien/films/${film}`, admin);
    rmSync(work, { recursive: true, force: true });
  });

  test("admin: AI job from the audio → drafts (de + uz + en) with live status, edit a line, approve, SRT download", async ({ page }) => {
    test.setTimeout(150_000);
    await adminLogin(page);
    await page.goto("/admin/medien/filme");
    await page.getByTestId("films-search").fill(`${TAG} Sprechfilm`);
    await page.getByTestId("film-edit").first().click();
    const ai = page.getByTestId("sub-ai");
    await expect(ai).toBeVisible();
    await expect(ai.getByTestId("sub-ai-stt")).toHaveAttribute("data-configured", "1");
    await expect(ai.getByTestId("sub-ai-translation")).toHaveAttribute("data-configured", "1");
    await expect(ai.getByTestId("sub-ai-language")).toHaveValue("de"); // the films are German: Deutsch is the default
    await expect(ai.getByTestId("sub-ai-agents")).toContainText("Korrektor");
    await expect(ai.getByTestId("sub-ai-auto-approve")).not.toBeChecked(); // drafts by default
    await expect(ai.getByTestId("sub-ai-target-uz")).toBeChecked(); // Uzbek is pre-selected
    await ai.getByTestId("sub-ai-target-en").check();
    await ai.getByTestId("sub-ai-start").click();
    await expect(ai.getByTestId("sub-ai-message")).toContainText("gestartet");
    const transcribe = ai.locator('[data-testid="sub-job"][data-kind="TRANSCRIBE"]');
    await expect(transcribe).toBeVisible();
    await expect(transcribe).toHaveAttribute("data-status", "COMPLETED", { timeout: 60_000 });
    await expect(transcribe).toContainText("Deutsch");
    await expect(transcribe).toHaveAttribute("data-gaps", "0");
    await expect(transcribe.getByTestId("sub-job-agents")).toContainText(/Hörer: \d+ Abschnitte · Korrektor: \d+ Zeilen verbessert/); // the proofreader fixed "testsatz"
    for (const l of ["uz", "en"]) await expect(ai.locator(`[data-testid="sub-job"][data-kind="TRANSLATE"][data-language="${l}"]`)).toHaveAttribute("data-status", "COMPLETED", { timeout: 60_000 });
    await page.screenshot({ path: "test-results/ai-subtitles-admin.png", fullPage: true });

    // the cards show the drafts (reloaded when the jobs finished); students do not get them yet
    for (const l of ["de", "uz", "en"]) await expect(page.locator(`[data-testid="film-subtitle"][data-language="${l}"]`)).toHaveAttribute("data-status", "DRAFT", { timeout: 15_000 });
    await expect(page.getByTestId("sub-source-de")).toContainText("KI-Transkript");
    await expect(page.getByTestId("sub-source-uz")).toContainText("aus Deutsch");
    const studentToken = await token(student, PASSWORD);
    expect((await call("POST", `/medien/films/${film}/watch`, studentToken)).json.subtitles).toEqual([]);

    // edit the first German line, keep the times
    await page.getByTestId("sub-edit-de").click();
    const editor = page.getByTestId("sub-editor");
    await expect(editor).toBeVisible();
    await editor.getByTestId("sub-editor-text").first().fill("Ich möchte heute ins Kino gehen.");
    await editor.getByTestId("sub-editor-save").click();
    await expect(page.getByTestId("film-note")).toHaveText("Änderungen gespeichert.");
    await expect(editor).toHaveCount(0);

    // approve German (one click on the job card) and Uzbek (on the track card); English stays a draft
    await transcribe.getByTestId("sub-job-approve").click();
    await expect(page.getByTestId("sub-state-de")).toHaveText("Freigegeben");
    await expect(transcribe.getByTestId("sub-job-approve")).toHaveCount(0);
    await expect(transcribe).toContainText("freigegeben, im Film-Player sichtbar");
    await page.getByTestId("sub-approve-uz").click();
    await expect(page.getByTestId("sub-state-uz")).toHaveText("Freigegeben");
    await expect(page.getByTestId("sub-state-en")).toContainText("Entwurf");
    const watch = (await call("POST", `/medien/films/${film}/watch`, studentToken)).json;
    expect(watch.subtitles.map((s: { language: string }) => s.language).sort()).toEqual(["de", "uz"]);
    expect(watch.original_language).toBe("de");

    // SRT download of the edited track
    const [download] = await Promise.all([page.waitForEvent("download"), page.getByTestId("sub-download-srt-de").click()]);
    expect(download.suggestedFilename()).toMatch(/\.srt$/);
    const srt = readFileSync((await download.path())!, "utf8");
    expect(srt).toMatch(/^1\n00:00:0\d,\d{3} --> 00:00:0\d,\d{3}\nIch möchte heute ins Kino gehen\./);
  });

  test("student: original (top) + translation (below) at the same time, each switched on / off, in sync with the video", async ({ page }) => {
    test.setTimeout(120_000);
    const adminToken = admin;
    const tracks = (await call("GET", `/admin/medien/films/${film}`, adminToken)).json.subtitles as { id: string; language: string }[];
    const de = (await call("GET", `/admin/medien/films/${film}/subtitles/${tracks.find((t) => t.language === "de")!.id}`, adminToken)).json.cues as [number, number, string][];
    await studentLogin(page, student);
    await page.goto(`/medien/filme/${film}`);
    const player = page.getByTestId("film-player");
    await expect(player).toBeVisible({ timeout: 25_000 });
    const video = player.getByTestId("film-video");
    await expect.poll(() => video.evaluate((v: HTMLVideoElement) => v.duration), { timeout: 30_000 }).toBeGreaterThan(15);
    const seek = (ms: number) => video.evaluate((v: HTMLVideoElement, s: number) => { v.currentTime = s; v.pause(); }, ms / 1000);
    const shown = async () => (await page.getByTestId("film-cue-line").allTextContents()).map((t) => t.trim());

    await seek(de[0][0] + 200);
    await expect.poll(shown).toEqual(["Ich möchte heute ins Kino gehen."]); // the original starts alone
    await player.hover({ position: { x: 200, y: 100 } });
    await page.getByTestId("film-subtitles").click();
    const menu = page.getByTestId("film-subtitle-menu");
    await expect(menu.getByTestId("sub-switches")).toBeVisible();
    await expect(menu.getByTestId("sub-original")).toBeChecked();
    await expect(menu.getByTestId("sub-translation")).not.toBeChecked();
    await menu.getByTestId("sub-translation").check();
    await expect.poll(shown).toEqual(["Ich möchte heute ins Kino gehen.", "[uz] Testsatz 1"]); // original on top, translation below
    await expect(page.locator('[data-testid="film-cue-line"]').first()).toHaveAttribute("data-language", "de");
    await page.screenshot({ path: "test-results/ai-subtitles-dual.png" });
    await menu.getByTestId("sub-original").uncheck();
    await expect.poll(shown).toEqual(["[uz] Testsatz 1"]);
    await menu.getByTestId("sub-original").check();
    await menu.getByTestId("sub-translation").uncheck();
    await expect.poll(shown).toEqual(["Ich möchte heute ins Kino gehen."]);
    await menu.getByTestId("sub-translation").check();
    // sync: each cue appears exactly in its time range and nothing in a gap
    await seek(de[1][0] + 100);
    await expect.poll(shown).toEqual([de[1][2], `[uz] ${de[1][2]}`]);
    const gap = de.findIndex((c, i) => i + 1 < de.length && de[i + 1][0] - c[1] > 300);
    if (gap >= 0) {
      await seek(de[gap][1] + 150);
      await expect.poll(shown).toEqual([]);
    }
    await seek(de[de.length - 1][1] - 100);
    await expect.poll(shown).toEqual([de[de.length - 1][2], `[uz] ${de[de.length - 1][2]}`]);
  });

  test("admin: 'sofort freigeben' + replace → the new German text and its translation go straight to the player", async ({ page }) => {
    test.setTimeout(120_000);
    await adminLogin(page);
    await page.goto("/admin/medien/filme");
    await page.getByTestId("films-search").fill(`${TAG} Sprechfilm`);
    await page.getByTestId("film-edit").first().click();
    const ai = page.getByTestId("sub-ai");
    await expect(ai.getByTestId("sub-ai-language")).toHaveValue("de");
    await ai.getByTestId("sub-ai-replace").check();
    await ai.getByTestId("sub-ai-auto-approve").check();
    await ai.getByTestId("sub-ai-start").click();
    await expect(ai.getByTestId("sub-ai-message")).toContainText("gestartet");
    const transcribe = ai.locator('[data-testid="sub-job"][data-kind="TRANSCRIBE"]').first(); // newest first
    await expect(transcribe).toHaveAttribute("data-status", "COMPLETED", { timeout: 60_000 });
    await expect(ai.locator('[data-testid="sub-job"][data-kind="TRANSLATE"][data-language="uz"]').first()).toHaveAttribute("data-status", "COMPLETED", { timeout: 60_000 });
    await expect(transcribe).toContainText("freigegeben, im Film-Player sichtbar", { timeout: 15_000 });
    await expect(transcribe.getByTestId("sub-job-approve")).toHaveCount(0);
    for (const l of ["de", "uz"]) await expect(page.locator(`[data-testid="film-subtitle"][data-language="${l}"]`)).toHaveAttribute("data-status", "APPROVED", { timeout: 15_000 });
    await expect(page.getByTestId("sub-state-en")).toContainText("Entwurf"); // not part of this job

    const tracks = (await call("GET", `/admin/medien/films/${film}`, admin)).json.subtitles as { id: string; language: string }[];
    const cues = async (l: string) => (await call("GET", `/admin/medien/films/${film}/subtitles/${tracks.find((t) => t.language === l)!.id}`, admin)).json.cues as [number, number, string][];
    expect((await cues("de"))[0][2]).toBe("Testsatz 1"); // replaced (the hand edit was overwritten on purpose), proofread
    expect((await cues("uz"))[0][2]).toBe("[uz] Testsatz 1");
    const watch = (await call("POST", `/medien/films/${film}/watch`, await token(student, PASSWORD))).json;
    expect(watch.subtitles.map((s: { language: string }) => s.language).sort()).toEqual(["de", "uz"]);
  });
});

// ---------------------------------------------------------------------------------------------------------------------------------------------------
test.describe.serial("Bibliothek bookshelf + book reader", () => {
  let admin = "";
  let student = "";
  const cats: string[] = [];
  const books: Record<string, string> = {};

  test.beforeAll(async () => {
    admin = await token(ADMIN.email, ADMIN.password);
    student = await createStudent();
    for (const name of ["Literatur", "Grammatik"]) {
      const made = await call("POST", "/admin/medien/categories", admin, { kind: "BOOK", name: `${TAG} ${name}`, sort_order: cats.length });
      expect(made.status, JSON.stringify(made.json)).toBe(200);
      cats.push(made.json.id);
    }
    const book = async (key: string, title: string, category: string, opts: { paid?: boolean } = {}) => {
      const made = await call("POST", "/admin/medien/books", admin, { title, author: `Autor ${key}`, language: "de", level: "A2", status: "PUBLISHED", category_id: category,
        ...(opts.paid ? { access_type: "PAID", price: 45000 } : {}) });
      expect(made.status, JSON.stringify(made.json)).toBe(200);
      await upload(`/admin/medien/books/${made.json.id}/file`, admin, pdf(15), "buch.pdf", "application/pdf");
      books[key] = made.json.id;
    };
    await book("free", `${TAG} Roman Frei`, cats[0]);
    await book("paid", `${TAG} Roman Kauf`, cats[0], { paid: true });
    await book("gram", `${TAG} Grammatik Frei`, cats[1]);
  });
  test.afterAll(async () => {
    for (const id of Object.values(books)) await call("DELETE", `/admin/medien/books/${id}`, admin);
    for (const id of cats) await call("DELETE", `/admin/medien/categories/${id}`, admin);
  });

  test("shelves: one per category, books side by side, title / author / free / price + lock, vertical only", async ({ page, isMobile }) => {
    await studentLogin(page, student);
    await page.goto("/medien/bibliothek");
    await page.getByTestId("book-search").fill(TAG);
    await expect(page.getByTestId("book-card")).toHaveCount(3, { timeout: 20_000 });
    const sections = page.getByTestId("shelf-section");
    await expect(sections).toHaveCount(2);
    await expect(sections.nth(0)).toContainText(`${TAG} Literatur`);
    await expect(sections.nth(0)).toContainText("2 Bücher");
    await expect(sections.nth(1)).toContainText(`${TAG} Grammatik`);
    const lit = sections.nth(0);
    await expect(lit.getByTestId("book-label").filter({ hasText: `${TAG} Roman Kauf` })).toContainText("Autor paid");
    await expect(lit.locator(`[data-testid="book-card"][data-locked="1"]`).getByTestId("book-sign-locked")).toContainText("45.000");
    await expect(lit.locator(`[data-testid="book-card"][data-free="1"]`).getByTestId("book-sign-free")).toBeVisible();
    // the two books of a category stand side by side on one board, the covers keep the 2:3 book shape and are not tiny
    const boxes = await lit.getByTestId("book-card").evaluateAll((els) => els.map((e) => { const r = e.querySelector('[class*="aspect-[2/3]"]')!.getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height }; }));
    expect(Math.abs(boxes[0].y - boxes[1].y)).toBeLessThan(4);
    expect(boxes[1].x).toBeGreaterThan(boxes[0].x + boxes[0].w);
    for (const b of boxes) { expect(b.w).toBeGreaterThanOrEqual(isMobile ? 85 : 100); expect(Math.abs(b.h / b.w - 1.5)).toBeLessThan(0.05); }
    expect(Number(await page.getByTestId("shelf").first().getAttribute("data-columns"))).toBeGreaterThanOrEqual(3);
    await noHorizontalScroll(page);
    await page.screenshot({ path: `test-results/bibliothek-shelves-${isMobile ? "phone" : "desktop"}.png`, fullPage: true });
  });

  test("reader on a computer: book mode, keys, click zones, buttons, zoom, 'close the book' → Bibliothek, resume", async ({ page, isMobile }) => {
    test.skip(isMobile, "desktop");
    test.setTimeout(90_000);
    await studentLogin(page, student);
    await page.goto(`/medien/bibliothek/${books.free}`);
    await page.getByTestId("book-read").click();
    const reader = page.getByTestId("pdf-reader");
    await expect(reader.getByTestId("reader-canvas")).toBeVisible({ timeout: 30_000 });
    await expect(reader).toHaveAttribute("data-mode", "book");
    await expect(reader.getByTestId("reader-total")).toHaveText("/ 15");
    const pageBox = reader.getByTestId("reader-page");
    await page.keyboard.press("ArrowRight");
    await expect(pageBox).toHaveValue("2");
    const stage = reader.getByTestId("reader-book");
    const box = (await stage.boundingBox())!;
    await page.mouse.click(box.x + box.width * 0.9, box.y + box.height / 2); // right third: forward
    await expect(pageBox).toHaveValue("3");
    await page.mouse.click(box.x + box.width * 0.1, box.y + box.height / 2); // left third: back
    await expect(pageBox).toHaveValue("2");
    await reader.getByTestId("reader-next").click();
    await reader.getByTestId("reader-next").click(); // a second click during the page animation still turns once more
    await expect(pageBox).toHaveValue("4");
    await expect(stage).toHaveAttribute("data-turning", "");
    await expect(reader.getByTestId("reader-percent")).toContainText("27%");
    await reader.getByTestId("reader-zoom-in").click();
    await expect(reader.getByTestId("reader-zoom")).toHaveText("125%");
    await expect(stage).toHaveAttribute("data-scale", "1.25");
    await reader.getByTestId("reader-zoom").click();
    await expect(stage).toHaveAttribute("data-scale", "1.00");
    await page.waitForTimeout(1300); // the position is saved (debounced)
    await expect(reader.getByTestId("reader-exit")).toBeVisible();
    await reader.getByTestId("reader-exit").click();
    await expect(page).toHaveURL(/\/medien\/bibliothek$/);
    await expect(page.getByTestId("pdf-reader")).toHaveCount(0);
    await page.goto(`/medien/bibliothek/${books.free}`);
    await expect(page.getByTestId("book-read")).toContainText("4");
    await page.getByTestId("book-read").click();
    await expect(page.getByTestId("reader-page")).toHaveValue("4", { timeout: 30_000 });
  });

  test("reader on a phone: swipe turns pages, pinch zooms without turning, double tap, big buttons, preview paywall, exit", async ({ page, isMobile }) => {
    test.skip(!isMobile, "phone");
    test.setTimeout(90_000);
    await studentLogin(page, student, "uz");
    await page.goto(`/medien/bibliothek/${books.gram}`);
    await page.getByTestId("book-read").click();
    const reader = page.getByTestId("pdf-reader");
    await expect(reader.getByTestId("reader-canvas")).toBeVisible({ timeout: 30_000 });
    await expect(reader).toHaveAttribute("data-mode", "book");
    await expect(reader.getByTestId("reader-hint")).toBeVisible(); // first time on a touch screen
    const stage = reader.getByTestId("reader-book");
    const pageBox = reader.getByTestId("reader-page");
    await swipe(page, 0.85, 0.15); // right to left: next page
    await expect(pageBox).toHaveValue("2");
    await swipe(page, 0.85, 0.15);
    await expect(pageBox).toHaveValue("3");
    await swipe(page, 0.15, 0.85); // left to right: back
    await expect(pageBox).toHaveValue("2");
    await swipe(page, 0.55, 0.5); // a small, slow movement does not turn
    await expect(pageBox).toHaveValue("2");
    // two fingers spread apart: zoom, never a page turn — even though the fingers also moved sideways
    await gesture(page, [
      { type: "pointerdown", id: 1, x: 0.45, y: 0.5 }, { type: "pointerdown", id: 2, x: 0.55, y: 0.5 },
      { type: "pointermove", id: 1, x: 0.35, y: 0.5 }, { type: "pointermove", id: 2, x: 0.75, y: 0.5 },
      { type: "pointermove", id: 1, x: 0.2, y: 0.5 }, { type: "pointermove", id: 2, x: 0.8, y: 0.5 },
      { type: "pointerup", id: 1, x: 0.2, y: 0.5 }, { type: "pointerup", id: 2, x: 0.8, y: 0.5 },
    ]);
    await expect.poll(async () => Number(await stage.getAttribute("data-scale"))).toBeGreaterThan(2);
    await expect(pageBox).toHaveValue("2");
    // one finger on a zoomed page moves it — still no turn
    await swipe(page, 0.8, 0.2);
    await expect(pageBox).toHaveValue("2");
    await expect.poll(async () => Number(await stage.getAttribute("data-scale"))).toBeGreaterThan(2);
    // double tap: the whole page again
    await gesture(page, [{ type: "pointerdown", id: 1, x: 0.5, y: 0.5 }, { type: "pointerup", id: 1, x: 0.5, y: 0.5 },
      { type: "pointerdown", id: 1, x: 0.5, y: 0.5 }, { type: "pointerup", id: 1, x: 0.5, y: 0.5 }], 60);
    await expect(stage).toHaveAttribute("data-scale", "1.00");
    // the big buttons at the bottom
    await expect(reader.getByTestId("reader-bottom-bar")).toBeVisible();
    const next = (await reader.getByTestId("reader-next-bottom").boundingBox())!;
    expect(next.height).toBeGreaterThanOrEqual(44);
    await reader.getByTestId("reader-next-bottom").click();
    await expect(pageBox).toHaveValue("3");
    await expect(reader.getByTestId("reader-position")).toHaveText("3 / 15");
    await noHorizontalScroll(page);
    await page.screenshot({ path: "test-results/reader-phone.png" });
    await page.waitForTimeout(1300);
    await reader.getByTestId("reader-exit").click();
    await expect(page).toHaveURL(/\/medien\/bibliothek$/);

    // a paid book: swipe past the last free page → the purchase window, never page 11
    await page.goto(`/medien/bibliothek/${books.paid}`);
    await page.getByTestId("book-preview").click();
    await expect(reader.getByTestId("reader-canvas")).toBeVisible({ timeout: 30_000 });
    await expect(reader.getByTestId("reader-total")).toHaveText("/ 15");
    await pageBox.fill("10");
    await pageBox.press("Enter");
    await expect(pageBox).toHaveValue("10");
    await swipe(page, 0.85, 0.15);
    await expect(reader.getByTestId("reader-paywall")).toBeVisible();
    await expect(pageBox).toHaveValue("10");
  });
});
