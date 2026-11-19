import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { expect, test, type Page } from "@playwright/test";

import { ADMIN, API_URL, PASSWORD, createStudent, loginViaForm } from "./helpers";

// VIZU MEDIENWELT film player: subtitles (de / uz / en / off), dual subtitles, synchronisation, speed, quality, fullscreen, keyboard,
// the student's subtitle settings (saved in the profile), clickable words with the dictionary card, continue watching, paid access, the
// admin subtitle manager, and the phone layout. Real files (ffmpeg video, SRT / VTT), local stack only (needs FFMPEG_BIN and psql).
const FFMPEG = process.env.FFMPEG_BIN ?? "ffmpeg";
const PSQL = process.env.E2E_PSQL ?? "C:/Program Files/PostgreSQL/18/bin/psql.exe";
const DB = process.env.E2E_DB ?? "vizu_gcr_e2e";
const PNG = Buffer.from("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082", "hex");

// the five cues of the test film (ms) — the sync checks compare the screen with this table
const CUES: [number, number][] = [[500, 3000], [3500, 5500], [6000, 9000], [10000, 14000], [15000, 19000]];
const srt = (texts: string[]) => texts.map((t, i) => {
  const ts = (ms: number) => `00:00:${String(Math.floor(ms / 1000)).padStart(2, "0")},${String(ms % 1000).padStart(3, "0")}`;
  return `${i + 1}\n${ts(CUES[i][0])} --> ${ts(CUES[i][1])}\n${t}\n`;
}).join("\n");
const DE = ["Der Zqxhund zqxlerne jeden Tag Deutsch.", "Auf Wiedersehen, Xyzzyfoo!", "Ich lerne Deutsch mit Filmen.", "Das ist der vierte Satz.", "Und hier endet der Film."];
const UZ = ["Zqxit har kuni nemis tilini o'rganadi.", "Xayr!", "Men filmlar bilan nemis tilini o'rganaman.", "Bu to'rtinchi gap.", "Film shu yerda tugaydi."];
const EN = ["The Zqxhund learns German every day.", "Goodbye!", "I learn German with films.", "This is the fourth sentence.", "And here the film ends."];
const SRT_DE = srt(DE);
const SRT_EN = srt(EN);
const VTT_UZ = `WEBVTT\n\n${UZ.map((t, i) => {
  const ts = (ms: number) => `00:${String(Math.floor(ms / 1000)).padStart(2, "0")}.${String(ms % 1000).padStart(3, "0")}`;
  return `${ts(CUES[i][0])} --> ${ts(CUES[i][1])}\n${t}\n`;
}).join("\n")}`;
const SRT_LONG = "1\n00:04:50,000 --> 00:05:00,000\nViel zu spaet\n";

const TAG = `FP${Date.now().toString(36)}`;
const work = mkdtempSync(join(tmpdir(), "film-player-"));
function ffmpeg(args: string[]) { execFileSync(FFMPEG, ["-nostdin", "-v", "error", "-y", ...args], { stdio: "pipe" }); }
const mp4 = (() => {
  let cache: Buffer | null = null;
  return () => {
    if (!cache) {
      const p = join(work, "film.mp4");
      ffmpeg(["-f", "lavfi", "-i", "testsrc=duration=20:size=320x180:rate=15", "-f", "lavfi", "-i", "sine=frequency=440:duration=20", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", p]);
      cache = readFileSync(p);
    }
    return cache;
  };
})();
function sql(q: string) { return execFileSync(PSQL, ["-h", "127.0.0.1", "-p", "54329", "-U", "postgres", "-d", DB, "-tAc", q], { encoding: "utf8" }).trim(); }

async function login(email: string, password: string) {
  const res = await fetch(`${API_URL}/api/v1/auth/login`, { method: "POST", headers: { "Content-Type": "application/json", "X-Forwarded-For": `10.98.${Math.floor(Math.random() * 250)}.${Math.floor(Math.random() * 250)}` }, body: JSON.stringify({ identifier: email, password }) });
  expect(res.status, await res.clone().text()).toBe(200);
  return (await res.json()).access_token as string;
}
const call = async (method: string, url: string, bearer: string, body?: unknown) => {
  const res = await fetch(`${API_URL}/api/v1${url}`, { method, headers: { Authorization: `Bearer ${bearer}`, ...(body ? { "Content-Type": "application/json" } : {}) }, body: body ? JSON.stringify(body) : undefined });
  const text = await res.text();
  return { status: res.status, json: text && res.headers.get("content-type")?.includes("json") ? JSON.parse(text) : null };
};
async function form(url: string, bearer: string, fields: Record<string, string | Blob>, names: Record<string, string> = {}) {
  const f = new FormData();
  for (const [k, v] of Object.entries(fields)) { if (typeof v === "string") f.append(k, v); else f.append(k, v, names[k]); }
  const res = await fetch(`${API_URL}/api/v1${url}`, { method: "POST", headers: { Authorization: `Bearer ${bearer}` }, body: f });
  expect(res.status, `${url}: ${await res.clone().text()}`).toBe(200);
  return res.json();
}

interface Fixtures { token: string; main: string; before: string; after: string; plain: string; onlyDe: string; premium: string; cats: string[] }
async function createFixtures(adminToken: string): Promise<Fixtures> {
  const cats = (await call("GET", "/admin/medien/categories?kind=FILM", adminToken)).json as { id: string; name: string }[];
  const category = cats.find((c) => c.name === "Kurzfilme")!.id;
  const film = async (name: string, extra: Record<string, unknown> = {}, subs: Record<string, [string, string]> = {}, video = true) => {
    const made = (await call("POST", "/admin/medien/films", adminToken, { title: `${TAG} ${name}`, level: "B1", status: "PUBLISHED", duration_minutes: 1, ...extra })).json;
    await form(`/admin/medien/films/${made.id}/cover`, adminToken, { file: new Blob([PNG], { type: "image/png" }) }, { file: "p.png" });
    if (video) await form(`/admin/medien/films/${made.id}/video`, adminToken, { file: new Blob([mp4()], { type: "video/mp4" }) }, { file: "v.mp4" });
    for (const [lang, [body, fileName]] of Object.entries(subs)) await form(`/admin/medien/films/${made.id}/subtitles`, adminToken, { language: lang, file: new Blob([body], { type: "text/plain" }) }, { file: fileName });
    return made.id as string;
  };
  const all = { de: [SRT_DE, "de.srt"], uz: [VTT_UZ, "uz.vtt"], en: [SRT_EN, "en.srt"] } as Record<string, [string, string]>;
  const before = await film("A Anfang", { category_id: category }, all);          // oldest of the series -> "next" of the main film
  const main = await film("B Hauptfilm", { category_id: category, is_featured: true }, all);
  const after = await film("C Ende", { category_id: category }, { de: [SRT_DE, "de.srt"] });  // newest -> "previous" of the main film
  const plain = await film("Ohne Untertitel");
  const onlyDe = await film("Nur Deutsch", {}, { de: [SRT_DE, "de.srt"] });
  const premium = await film("Premium", { access_type: "PAID", price: 90000 }, { de: [SRT_DE, "de.srt"], uz: [VTT_UZ, "uz.vtt"] });
  // an extra quality (360p) of the main film through the chunked upload
  const data = mp4();
  const init = (await call("POST", `/admin/medien/films/${main}/video/init`, adminToken, { filename: "360.mp4", size: data.length, quality: "360p" })).json;
  for (let i = 0; i < init.chunks; i += 1) {
    const res = await fetch(`${API_URL}/api/v1/admin/medien/films/${main}/video/${init.upload_id}/${i}`, { method: "PUT", headers: { Authorization: `Bearer ${adminToken}`, "Content-Type": "application/octet-stream" }, body: data.subarray(i * init.chunk_size, (i + 1) * init.chunk_size) });
    expect(res.status).toBe(200);
  }
  expect((await call("POST", `/admin/medien/films/${main}/video/${init.upload_id}/complete`, adminToken)).status).toBe(200);
  // dictionary entries with words nobody else uses
  const sid = 700_000 + Math.floor(Math.random() * 90_000);
  sql(`INSERT INTO dictionary_entries (id, level, source_id, lemma, word_type, article, translation, status, group_key, search_de, search_uz, search_forms, content_hash, example_de, example_uz, extra, is_primary, is_published)
       VALUES (gen_random_uuid(), 'C1', ${sid}, 'Zqxhund', 'Nomen', 'der', 'zqxit', 'verified', 'e2e-${TAG}-a', 'zqxhund', '|zqxit|', '|zqxhunde|zqxhundes|', 'x', 'Der Zqxhund schlaeft.', 'Zqxit uxlaydi.', '{}'::jsonb, true, true),
              (gen_random_uuid(), 'C1', ${sid + 1}, 'zqxlernen', 'Verb', NULL, 'zqxorganmoq', 'verified', 'e2e-${TAG}-b', 'zqxlernen', '|zqxorganmoq|', '|zqxlerne|zqxlernst|zqxlernt|', 'x', 'Ich zqxlerne gern.', 'Men zqxorganaman.', '{}'::jsonb, true, true)`);
  return { token: adminToken, main, before, after, plain, onlyDe, premium, cats: [category] };
}
async function removeFixtures(fx: Fixtures) {
  for (const id of [fx.main, fx.before, fx.after, fx.plain, fx.onlyDe, fx.premium]) await call("DELETE", `/admin/medien/films/${id}`, fx.token);
  sql(`DELETE FROM dictionary_entries WHERE group_key LIKE 'e2e-${TAG}-%'`);
}

async function studentLogin(page: Page, email: string) {
  await loginViaForm(page, email, PASSWORD);
  await expect(page).toHaveURL(/\/dashboard/);
  await page.evaluate(() => localStorage.setItem("vizu-language", JSON.stringify({ state: { language: "de" }, version: 0 })));
}
async function adminLogin(page: Page) {
  await page.addInitScript(() => localStorage.setItem("vizu-language", JSON.stringify({ state: { language: "de" }, version: 0 })));
  await loginViaForm(page, ADMIN.email, ADMIN.password);
  await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
  await page.getByRole("button", { name: "Bestätigen" }).click();
  await expect(page).toHaveURL(/\/admin/);
}
async function openFilm(page: Page, id: string) {
  await page.goto(`/medien/filme/${id}`);
  const player = page.getByTestId("film-player");
  await expect(player).toBeVisible({ timeout: 25_000 });
  await expect.poll(() => player.getByTestId("film-video").evaluate((v: HTMLVideoElement) => v.duration), { timeout: 30_000 }).toBeGreaterThan(15);
  return player;
}
const video = (page: Page) => page.getByTestId("film-video");
const seek = (page: Page, seconds: number) => video(page).evaluate((v: HTMLVideoElement, s: number) => { v.currentTime = s; v.pause(); }, seconds);
const lines = (page: Page) => page.getByTestId("film-cue-line");
const lineTexts = async (page: Page) => (await lines(page).allTextContents()).map((t) => t.trim());
/** a control click while the bar may be faded out (playing): wake it with the pointer first */
async function ctl(page: Page, id: string) {
  await page.getByTestId("film-player").hover({ position: { x: 240, y: 120 } });
  await page.getByTestId(id).click();
}
async function pickSubtitle(page: Page, language: string) {
  await ctl(page, "film-subtitles");
  await (language === "off" ? page.getByTestId("film-subtitle-off") : page.locator(`[data-testid="film-subtitle-option"][data-language="${language}"]`)).click();
}
async function openMenu(page: Page) {
  await ctl(page, "film-subtitles");
  await expect(page.getByTestId("film-subtitle-menu")).toBeVisible();
}
async function closeMenu(page: Page) {
  await page.getByTestId("film-subtitles").click();
  await expect(page.getByTestId("film-subtitle-menu")).toHaveCount(0);
}
async function noHorizontalScroll(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
}
async function prefsOf(email: string) { return (await call("GET", "/medien/player-prefs", await login(email, PASSWORD))).json; }

test.use({ launchOptions: { args: ["--autoplay-policy=no-user-gesture-required"] } });

test.describe.serial("Film player (desktop)", () => {
  test.skip(({ isMobile }) => isMobile, "the phone layout runs in its own test");
  let fx: Fixtures;
  let student = "";
  let adminToken = "";

  test.beforeAll(async () => {
    test.setTimeout(180_000);
    student = await createStudent();
    adminToken = await login(ADMIN.email, ADMIN.password);
    fx = await createFixtures(adminToken);
  });
  test.afterAll(async () => {
    if (fx) await removeFixtures(fx);
    rmSync(work, { recursive: true, force: true });
  });

  test("admin: sections, subtitle check / upload / preview / language / delete, extra quality", async ({ page }) => {
    test.setTimeout(150_000);
    const made = (await call("POST", "/admin/medien/films", adminToken, { title: `${TAG} Admin`, level: "B1", status: "DRAFT", duration_minutes: 1 })).json;
    await form(`/admin/medien/films/${made.id}/video`, adminToken, { file: new Blob([mp4()], { type: "video/mp4" }) }, { file: "v.mp4" });
    try {
      await adminLogin(page);
      await page.goto("/admin/medien/filme");
      await page.getByTestId("films-search").fill(`${TAG} Admin`);
      await page.getByTestId("film-edit").first().click();
      const d = page.getByTestId("film-dialog");
      for (const s of ["info", "video", "subtitles", "access"]) await expect(page.getByTestId(`section-${s}`)).toBeVisible();
      await expect(page.getByTestId("film-stream-ready")).toContainText("Bereit für Streaming");
      await expect(page.getByTestId("film-video-readiness")).toContainText("MP4");
      // not a subtitle: refused by the check, nothing is stored
      await d.getByTestId("sub-file-de").setInputFiles({ name: "x.srt", mimeType: "text/plain", buffer: Buffer.from([0, 1, 2, 3, 4, 5]) });
      await page.getByTestId("sub-check-de").click();
      await expect(page.getByTestId("sub-check-error-de")).toContainText("keine Textdatei");
      await d.getByTestId("sub-file-de").setInputFiles({ name: "x.ass", mimeType: "text/plain", buffer: Buffer.from("[Script Info]") });
      await page.getByTestId("sub-check-de").click();
      await expect(page.getByTestId("sub-check-error-de")).toContainText("Dateiformat");
      await expect(page.getByTestId("sub-status-de")).toHaveText("Nicht vorhanden");
      // a good file: report first, then upload
      await d.getByTestId("sub-file-de").setInputFiles({ name: "de.srt", mimeType: "text/plain", buffer: Buffer.from(SRT_DE) });
      await page.getByTestId("sub-check-de").click();
      await expect(page.getByTestId("sub-report-de")).toContainText("5 Zeilen");
      await expect(page.getByTestId("sub-report-de-warnings-ok")).toBeVisible();
      await page.getByTestId("sub-upload-de").click();
      await expect(page.getByTestId("sub-status-de")).toContainText("5 Zeilen", { timeout: 20_000 });
      await d.getByTestId("sub-file-uz").setInputFiles({ name: "uz.vtt", mimeType: "text/vtt", buffer: Buffer.from(VTT_UZ) });
      await page.getByTestId("sub-upload-uz").click();
      await expect(page.getByTestId("sub-status-uz")).toContainText("5 Zeilen", { timeout: 20_000 });
      // an English file that does not fit the video: reported (warning), still saved; then replaced by the right one
      await d.getByTestId("sub-file-en").setInputFiles({ name: "en.srt", mimeType: "text/plain", buffer: Buffer.from(SRT_LONG) });
      await page.getByTestId("sub-check-en").click();
      await expect(page.locator('[data-testid="sub-report-en-warnings"] [data-code="BEYOND_VIDEO"]')).toBeVisible();
      await page.getByTestId("sub-upload-en").click();
      await expect(page.getByTestId("sub-warn-count-en")).toBeVisible({ timeout: 20_000 });
      await d.getByTestId("sub-file-en").setInputFiles({ name: "en.srt", mimeType: "text/plain", buffer: Buffer.from(SRT_EN) });
      await page.getByTestId("sub-upload-en").click();
      await expect(page.getByTestId("sub-warn-count-en")).toHaveCount(0, { timeout: 20_000 });
      await expect(page.getByTestId("sub-status-en")).toContainText("5 Zeilen");
      // preview: the cue list and "what the student sees at this second"
      await page.getByTestId("sub-preview-de").click();
      await expect(page.getByTestId("sub-preview-panel")).toBeVisible();
      await expect(page.getByTestId("sub-preview-cue")).toHaveCount(5);
      await page.getByTestId("sub-preview-time").fill("1000");
      await expect(page.getByTestId("sub-preview-now")).toContainText("Zqxhund");
      await page.getByTestId("sub-preview-time").fill("3250");
      await expect(page.getByTestId("sub-preview-now")).toContainText("kein Untertitel");
      await page.getByTestId("sub-preview-cue").nth(2).click();
      await expect(page.getByTestId("sub-preview-now")).toContainText("Ich lerne Deutsch");
      await page.getByTestId("sub-preview-close").click();
      // assign another language to a track, then delete it
      await page.getByTestId("sub-lang-uz").selectOption({ label: "Русский" });
      await expect(page.getByTestId("film-note")).toContainText("Sprache geändert");
      await expect(page.locator('[data-testid="film-subtitle"][data-language="ru"]')).toHaveAttribute("data-present", "1"); // Russian has its own card (2026-11-19)
      await expect(page.getByTestId("sub-status-uz")).toHaveText("Nicht vorhanden");
      await page.getByTestId("sub-delete-ru").click();
      await expect(page.locator('[data-testid="film-subtitle"][data-language="ru"]')).toHaveAttribute("data-present", "0");
      await page.getByTestId("sub-delete-en").click();
      await expect(page.getByTestId("sub-status-en")).toHaveText("Nicht vorhanden");
      // an additional quality: upload, listed, deleted
      await page.getByTestId("film-quality-label").selectOption("480p");
      await d.getByTestId("film-quality-file").setInputFiles({ name: "480.mp4", mimeType: "video/mp4", buffer: mp4() });
      await page.getByTestId("film-quality-upload").click();
      await expect(page.getByTestId("film-note")).toHaveText("Qualität 480p gespeichert.", { timeout: 60_000 });
      await expect(page.getByTestId("film-rendition")).toHaveCount(1);
      await page.getByTestId("film-rendition-delete").click();
      await expect(page.getByTestId("film-rendition")).toHaveCount(0);
      await page.getByTestId("film-close").click();
    } finally {
      await call("DELETE", `/admin/medien/films/${made.id}`, adminToken);
    }
  });

  test("student: German / Uzbek / English / off — only the languages the film has", async ({ page }) => {
    await studentLogin(page, student);
    const player = await openFilm(page, fx.main);
    await expect(page.getByTestId("film-subtitle-langs")).toContainText("Deutsch");
    await seek(page, 1);
    await expect(lines(page)).toHaveCount(1);
    await expect(lines(page).first()).toHaveAttribute("data-language", "de");   // German on by default
    await expect(lines(page).first()).toContainText(DE[0]);
    await ctl(page, "film-subtitles");
    await expect(page.getByTestId("film-subtitle-option")).toHaveCount(3);
    expect(await page.getByTestId("film-subtitle-option").evaluateAll((els) => els.map((e) => e.getAttribute("data-language")))).toEqual(["de", "uz", "en"]);
    await page.locator('[data-testid="film-subtitle-option"][data-language="uz"]').click();
    await expect.poll(() => lineTexts(page)).toEqual([UZ[0]]);
    await pickSubtitle(page, "en");
    await expect.poll(() => lineTexts(page)).toEqual([EN[0]]);
    await pickSubtitle(page, "off");
    await expect(page.getByTestId("film-cue")).toHaveCount(0);
    await seek(page, 12);
    await expect(page.getByTestId("film-cue")).toHaveCount(0);
    await pickSubtitle(page, "de");
    await expect.poll(() => lineTexts(page)).toEqual([DE[3]]);
    // a film without subtitles: no language is offered, nothing to switch on
    await openFilm(page, fx.plain);
    await ctl(page, "film-subtitles");
    await expect(page.getByTestId("film-subtitle-option")).toHaveCount(0);
    await expect(page.getByTestId("film-no-subtitles")).toBeVisible();
    await expect(page.getByTestId("sub-dual")).toHaveCount(0);
    await seek(page, 1);
    await expect(page.getByTestId("film-cue")).toHaveCount(0);
    // one language only: that one, and dual subtitles cannot be switched on
    await openFilm(page, fx.onlyDe);
    await ctl(page, "film-subtitles");
    await expect(page.getByTestId("film-subtitle-option")).toHaveCount(1);
    await expect(page.getByTestId("sub-dual")).toBeDisabled();
    expect(player).toBeTruthy();
  });

  test("dual subtitles: German on top, the translation below, in step", async ({ page }) => {
    await studentLogin(page, student);
    await openFilm(page, fx.main);
    await openMenu(page);
    await page.getByTestId("sub-dual").check();
    await expect(page.getByTestId("sub-secondary")).toHaveValue("uz");
    await closeMenu(page);
    await seek(page, 1);
    await expect(page.getByTestId("film-cue")).toHaveAttribute("data-dual", "1");
    await expect.poll(() => lineTexts(page)).toEqual([DE[0], UZ[0]]);
    expect(await lines(page).evaluateAll((els) => els.map((e) => e.getAttribute("data-language")))).toEqual(["de", "uz"]);
    const [a, b] = await lines(page).evaluateAll((els) => els.map((e) => e.getBoundingClientRect().top));
    expect(a).toBeLessThan(b);
    // both lines change together on every seek and share the gaps
    for (const [sec, i] of [[4, 1], [7, 2], [12, 3], [17, 4], [1, 0]] as const) {
      await seek(page, sec);
      await expect.poll(() => lineTexts(page)).toEqual([DE[i], UZ[i]]);
    }
    await seek(page, 3.2);
    await expect(page.getByTestId("film-cue")).toHaveCount(0);
    // a different second language; German stays on top even when Uzbek is the chosen one
    await openMenu(page);
    await page.getByTestId("sub-secondary").selectOption("en");
    await closeMenu(page);
    await seek(page, 7);
    await expect.poll(() => lineTexts(page)).toEqual([DE[2], EN[2]]);
    await pickSubtitle(page, "uz");
    await openMenu(page);
    await page.getByTestId("sub-secondary").selectOption("de");
    await closeMenu(page);
    await seek(page, 7);
    await expect.poll(() => lineTexts(page)).toEqual([DE[2], UZ[2]]);
    // only the German line has clickable words
    await expect(page.locator('[data-testid="film-cue-line"][data-language="uz"] [data-word]')).toHaveCount(0);
    expect(await page.locator('[data-testid="film-cue-line"][data-language="de"] [data-word]').count()).toBeGreaterThan(2);
    // switching dual off leaves one line
    await openMenu(page);
    await page.getByTestId("sub-dual").uncheck();
    await closeMenu(page);
    await expect(page.getByTestId("film-cue")).toHaveAttribute("data-dual", "0");
    await expect.poll(() => lineTexts(page)).toEqual([UZ[2]]);
  });

  test("synchronisation: while playing at 0.5x / 1x / 2x, after seeking back and forth", async ({ page }) => {
    test.setTimeout(90_000);
    await studentLogin(page, student);
    await openFilm(page, fx.main);
    await pickSubtitle(page, "de"); // the film remembers the language of the last visit: choose explicitly
    const expectedAt = (ms: number) => { const i = CUES.findIndex(([s, e]) => ms >= s && ms < e); return i < 0 ? null : DE[i]; };
    const sample = (rate: number, from: number, seconds: number) => video(page).evaluate(async (v: HTMLVideoElement, args: { rate: number; from: number; seconds: number }) => {
      v.currentTime = args.from; v.playbackRate = args.rate;
      await v.play();
      const out: { t: number; text: string | null }[] = [];
      const end = performance.now() + args.seconds * 1000;
      while (performance.now() < end) {
        await new Promise((r) => requestAnimationFrame(r));
        out.push({ t: v.currentTime * 1000, text: document.querySelector('[data-testid="film-cue-line"]')?.textContent?.trim() ?? null });
      }
      v.pause();
      return out;
    }, { rate, from, seconds });
    const wrong = (samples: { t: number; text: string | null }[], margin: number) => samples.filter(({ t, text }) => {
      // the screen is one frame behind the clock at most: ignore the edges of a cue
      const near = CUES.some(([s, e]) => Math.abs(t - s) < margin || Math.abs(t - e) < margin);
      return !near && text !== expectedAt(t);
    });
    for (const [rate, from, seconds, margin] of [[1, 0, 3.5, 160], [2, 2.5, 3.2, 260], [0.5, 5, 3, 130]] as const) {
      const samples = await sample(rate, from, seconds);
      expect(samples.length).toBeGreaterThan(20);
      expect(wrong(samples, margin), `rate ${rate}`).toEqual([]);
      expect(new Set(samples.map((s) => s.text)).size, `rate ${rate} shows something`).toBeGreaterThan(1);
    }
    // seeking forward and back: the line follows at once, also while paused
    for (const [sec, want] of [[16, DE[4]], [1, DE[0]], [3.3, null], [7.5, DE[2]], [0.2, null], [10.1, DE[3]], [19.2, null]] as const) {
      await seek(page, sec);
      if (want) await expect.poll(() => lineTexts(page)).toEqual([want]); else await expect(page.getByTestId("film-cue")).toHaveCount(0);
    }
    // the speed menu changes the rate and the subtitle keeps following the video clock
    await ctl(page, "film-speed");
    await expect(page.getByTestId("film-speed-option")).toHaveCount(6);
    await page.getByTestId("film-speed-option").filter({ hasText: "0.75×" }).click();
    expect(await video(page).evaluate((v: HTMLVideoElement) => v.playbackRate)).toBe(0.75);
    await seek(page, 12);
    await expect.poll(() => lineTexts(page)).toEqual([DE[3]]);
  });

  test("controls: speed, quality, previous / next, ±10 s, fullscreen, shortcuts, Picture-in-Picture", async ({ page }) => {
    test.setTimeout(90_000);
    await studentLogin(page, student);
    const player = await openFilm(page, fx.main);
    await pickSubtitle(page, "de");
    // speeds
    for (const s of ["0.5", "0.75", "1", "1.25", "1.5", "2"]) {
      await ctl(page, "film-speed");
      await page.getByTestId("film-speed-option").filter({ hasText: new RegExp(`^${s}×$`) }).click();
      expect(await video(page).evaluate((v: HTMLVideoElement) => v.playbackRate)).toBe(Number(s));
    }
    await ctl(page, "film-speed");
    await page.getByTestId("film-speed-option").filter({ hasText: /^1×$/ }).click();
    // quality: original + 360p; switching keeps the position and the playing state
    await expect(page.getByTestId("film-quality")).toBeVisible();
    await video(page).evaluate((v: HTMLVideoElement) => { v.currentTime = 8; return v.play(); });
    await expect.poll(() => video(page).evaluate((v: HTMLVideoElement) => v.currentTime)).toBeGreaterThan(8.3);
    await ctl(page, "film-quality");
    await expect(page.getByTestId("film-quality-option")).toHaveCount(2);
    await page.getByTestId("film-quality-option").nth(1).click();
    await expect(video(page)).toHaveAttribute("data-source", /^(?!main$).+/);
    await expect.poll(() => video(page).evaluate((v: HTMLVideoElement) => v.currentSrc), { timeout: 15_000 }).toContain("/medien/rendition/");
    await expect.poll(() => video(page).evaluate((v: HTMLVideoElement) => v.readyState), { timeout: 15_000 }).toBeGreaterThan(1);
    expect(await video(page).evaluate((v: HTMLVideoElement) => v.currentTime)).toBeGreaterThan(7.5);
    await ctl(page, "film-quality");
    await page.getByTestId("film-quality-option").nth(0).click();
    await expect(video(page)).toHaveAttribute("data-source", "main");
    await expect.poll(() => video(page).evaluate((v: HTMLVideoElement) => v.currentTime), { timeout: 15_000 }).toBeGreaterThan(7.5);
    await video(page).evaluate((v: HTMLVideoElement) => v.pause());
    // ±10 s, volume, mute
    await seek(page, 5);
    await ctl(page, "film-fwd10");
    expect(Math.round(await video(page).evaluate((v: HTMLVideoElement) => v.currentTime))).toBe(15);
    await ctl(page, "film-back10");
    expect(Math.round(await video(page).evaluate((v: HTMLVideoElement) => v.currentTime))).toBe(5);
    await ctl(page, "film-mute");
    expect(await video(page).evaluate((v: HTMLVideoElement) => v.muted)).toBe(true);
    await ctl(page, "film-mute");
    // keyboard
    await page.mouse.move(5, 5);
    await page.keyboard.press("k");
    await expect.poll(() => video(page).evaluate((v: HTMLVideoElement) => v.paused)).toBe(false);
    await page.keyboard.press("k");
    await expect.poll(() => video(page).evaluate((v: HTMLVideoElement) => v.paused)).toBe(true);
    await seek(page, 5);
    await page.keyboard.press("ArrowRight");
    expect(Math.round(await video(page).evaluate((v: HTMLVideoElement) => v.currentTime))).toBe(10);
    await page.keyboard.press("j");
    expect(Math.round(await video(page).evaluate((v: HTMLVideoElement) => v.currentTime))).toBe(0);
    await page.keyboard.press("5");
    expect(Math.round(await video(page).evaluate((v: HTMLVideoElement) => v.currentTime / v.duration * 10))).toBe(5);
    await page.keyboard.press("m");
    expect(await video(page).evaluate((v: HTMLVideoElement) => v.muted)).toBe(true);
    await page.keyboard.press("m");
    await page.keyboard.press(">");
    expect(await video(page).evaluate((v: HTMLVideoElement) => v.playbackRate)).toBe(1.25);
    await page.keyboard.press("<");
    expect(await video(page).evaluate((v: HTMLVideoElement) => v.playbackRate)).toBe(1);
    await seek(page, 1);
    await expect(lines(page)).toHaveCount(1);
    await page.keyboard.press("c");
    await expect(page.getByTestId("film-cue")).toHaveCount(0);
    await page.keyboard.press("c");
    await expect(lines(page)).toHaveCount(1);
    await page.keyboard.press("d");
    await expect(page.getByTestId("film-cue")).toHaveAttribute("data-dual", "1");
    await page.keyboard.press("d");
    await page.keyboard.press("?");
    await expect(page.getByTestId("film-shortcuts")).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.getByTestId("film-shortcuts")).toHaveCount(0);
    // fullscreen (the player box itself, so the subtitles stay) and back
    await ctl(page, "film-fullscreen");
    await expect.poll(() => page.evaluate(() => !!document.fullscreenElement), { timeout: 8000 }).toBe(true);
    await expect(player).toHaveAttribute("data-fullscreen", "1");
    await expect(lines(page)).toHaveCount(1);
    await ctl(page, "film-fullscreen");
    await expect.poll(() => page.evaluate(() => !!document.fullscreenElement)).toBe(false);
    // Picture-in-Picture: offered when the browser can do it
    const pip = await page.evaluate(() => !!document.pictureInPictureEnabled);
    await expect(page.getByTestId("film-pip")).toHaveCount(pip ? 1 : 0);
    // previous / next film of the series (before = next, after = previous)
    await expect(page.getByTestId("film-prev")).toBeEnabled();
    await expect(page.getByTestId("film-next")).toBeEnabled();
    await ctl(page, "film-next");
    await expect(page).toHaveURL(new RegExp(`/medien/filme/${fx.before}$`), { timeout: 15_000 });
    await expect(page.getByTestId("film-title")).toContainText("A Anfang", { timeout: 15_000 });
    await expect(page.getByTestId("film-next")).toBeDisabled();
    await page.waitForTimeout(1200); // the shared page transition remounts the page once
    await page.keyboard.press("Shift+P");
    await expect(page).toHaveURL(new RegExp(`/medien/filme/${fx.main}$`), { timeout: 15_000 });
  });

  test("subtitle settings: size, colour, background, position, font, on / off — saved in the profile", async ({ page }) => {
    test.setTimeout(90_000);
    await studentLogin(page, student);
    await openFilm(page, fx.main);
    await seek(page, 1);
    const cue = page.getByTestId("film-cue");
    const read = (sel: "film-cue" | "film-cue-line", prop: string) => page.getByTestId(sel).first().evaluate((e, p) => getComputedStyle(e).getPropertyValue(p), prop);
    /** the computed value once it stopped changing (the theme animates colours for a moment) */
    const css = async (sel: "film-cue" | "film-cue-line", prop: string) => {
      let prev = await read(sel, prop);
      for (let i = 0; i < 12; i += 1) {
        await page.waitForTimeout(120);
        const now = await read(sel, prop);
        if (now === prev) return now;
        prev = now;
      }
      return prev;
    };
    await openMenu(page);
    const sizes: number[] = [];
    for (const s of ["small", "medium", "large"]) {
      await page.getByTestId(`sub-size-${s}`).click();
      await expect(page.getByTestId(`sub-size-${s}`)).toHaveAttribute("aria-pressed", "true");
      sizes.push(parseFloat(await css("film-cue", "font-size")));
    }
    expect(sizes[0]).toBeLessThan(sizes[1]);
    expect(sizes[1]).toBeLessThan(sizes[2]);
    await page.getByTestId("sub-color-7dd3fc").click();
    expect(await css("film-cue", "color")).toBe("rgb(125, 211, 252)");
    await page.getByTestId("sub-opacity").fill("30");
    expect(await css("film-cue-line", "background-color")).toBe("rgba(0, 0, 0, 0.3)");
    await expect(page.getByTestId("sub-opacity-value")).toHaveText("30%");
    await page.getByTestId("sub-font-mono").click();
    expect((await css("film-cue", "font-family")).toLowerCase()).toContain("mono");
    await page.getByTestId("sub-font-serif").click();
    expect((await css("film-cue", "font-family")).toLowerCase()).toContain("georgia");
    const bottomOf = async () => (await cue.boundingBox())!.y + (await cue.boundingBox())!.height;
    await page.getByTestId("sub-position-bottom").click();
    const low = await bottomOf();
    await page.getByTestId("sub-position-higher").click();
    expect(await bottomOf()).toBeLessThan(low - 20);
    await closeMenu(page);
    // saved on the server (the student's profile), a moment after the last change
    await expect.poll(() => prefsOf(student), { timeout: 15_000 }).toMatchObject({ size: "large", color: "#7dd3fc", bg_opacity: 30, font: "serif", position: "higher" });
    // after a reload the same look is applied
    await page.reload();
    await openFilm(page, fx.main);
    await seek(page, 1);
    expect(parseFloat(await css("film-cue", "font-size"))).toBe(sizes[2]);
    expect(await css("film-cue", "color")).toBe("rgb(125, 211, 252)");
    expect(await css("film-cue-line", "background-color")).toBe("rgba(0, 0, 0, 0.3)");
    // subtitles off is remembered too: the next film starts without them; on again
    await pickSubtitle(page, "off");
    await expect(page.getByTestId("film-cue")).toHaveCount(0);
    await expect.poll(() => prefsOf(student), { timeout: 15_000 }).toMatchObject({ enabled: false });
    await openFilm(page, fx.before);
    await seek(page, 1);
    await expect(page.getByTestId("film-cue")).toHaveCount(0);
    await pickSubtitle(page, "de");
    await expect.poll(() => lineTexts(page)).toEqual([DE[0]]);
    // restore the defaults for the later tests
    await openMenu(page);
    await page.getByTestId("sub-size-medium").click();
    await page.getByTestId("sub-color-ffffff").click();
    await page.getByTestId("sub-opacity").fill("75");
    await page.getByTestId("sub-font-sans").click();
    await page.getByTestId("sub-position-bottom").click();
    await expect.poll(() => prefsOf(student), { timeout: 15_000 }).toMatchObject({ size: "medium", color: "#ffffff", bg_opacity: 75, font: "sans", position: "bottom", enabled: true });
  });

  test("interactive subtitles: word card with translation, article, word type, example; save, copy, search, phrases", async ({ page, context }) => {
    test.setTimeout(90_000);
    await context.grantPermissions(["clipboard-read", "clipboard-write"]);
    await studentLogin(page, student);
    await openFilm(page, fx.main);
    await pickSubtitle(page, "de");
    // click a word while the film plays: the video pauses, the card shows the dictionary entry
    await video(page).evaluate((v: HTMLVideoElement) => { v.currentTime = 0.6; return v.play(); });
    await expect(lines(page)).toHaveCount(1);
    await page.locator('[data-testid="film-cue-line"] [data-word="Zqxhund"]').click();
    const popup = page.getByTestId("word-popup");
    await expect(popup).toBeVisible();
    expect(await video(page).evaluate((v: HTMLVideoElement) => v.paused)).toBe(true);
    await expect(popup.getByTestId("wp-word")).toHaveText("der Zqxhund");
    await expect(popup.getByTestId("wp-article")).toHaveText("der");
    await expect(popup.getByTestId("wp-type")).toHaveText("Nomen");
    await expect(popup.getByTestId("wp-translation")).toHaveText("zqxit");
    await expect(popup.getByTestId("wp-example")).toContainText("Zqxhund");
    await expect(popup.getByTestId("wp-sentence")).toContainText(DE[0]);
    // save (the Wörterbuch star), copy, close -> the film goes on
    const token = await login(student, PASSWORD);
    await popup.getByTestId("wp-save").click();
    await expect(popup.getByTestId("wp-save")).toHaveAttribute("aria-pressed", "true");
    await expect.poll(async () => JSON.stringify((await call("GET", "/dictionary/saved?q=zqxhund", token)).json)).toContain("Zqxhund");
    await popup.getByTestId("wp-copy").click();
    await expect.poll(() => page.evaluate(() => navigator.clipboard.readText())).toBe("der Zqxhund");
    await popup.getByTestId("wp-copy-sentence").click();
    await expect.poll(() => page.evaluate(() => navigator.clipboard.readText())).toBe(DE[0]);
    await popup.getByTestId("wp-save").click();
    await expect(popup.getByTestId("wp-save")).toHaveAttribute("aria-pressed", "false");
    await expect(popup.getByTestId("wp-open")).toHaveAttribute("href", "/woerterbuch");
    await popup.getByTestId("wp-close").click();
    await expect(popup).toHaveCount(0);
    await expect.poll(() => video(page).evaluate((v: HTMLVideoElement) => v.paused)).toBe(false);
    // an inflected form shows its headword
    await seek(page, 1);
    await page.locator('[data-testid="film-cue-line"] [data-word="zqxlerne"]').click();
    await expect(popup.getByTestId("wp-form")).toContainText("zqxlernen");
    await expect(popup.getByTestId("wp-translation")).toHaveText("zqxorganmoq");
    await page.keyboard.press("Escape");
    await expect(popup).toHaveCount(0);
    // not in the dictionary: no invented translation, a search is offered
    await seek(page, 4);
    await page.locator('[data-testid="film-cue-line"] [data-word="Xyzzyfoo"]').click();
    await expect(popup.getByTestId("wp-none")).toBeVisible();
    await expect(popup.getByTestId("wp-translation")).toHaveCount(0);
    await popup.getByTestId("wp-search-input").fill("Zqxhu");
    await popup.getByTestId("wp-search").click();
    await expect(popup.getByTestId("wp-result")).toContainText("Zqxhund");
    await popup.getByTestId("wp-result").first().click();
    await expect(popup.getByTestId("wp-translation")).toHaveText("zqxit");
    await popup.getByTestId("wp-close").click();
    // a selected phrase opens the card for the phrase, its words can be looked up one by one
    await seek(page, 1);
    await page.evaluate(() => {
      const spans = Array.from(document.querySelectorAll('[data-testid="film-cue-line"] [data-word]'));
      const range = document.createRange();
      range.setStartBefore(spans[0]);
      range.setEndAfter(spans[1]);
      const sel = window.getSelection()!;
      sel.removeAllRanges();
      sel.addRange(range);
    });
    await expect(popup).toBeVisible({ timeout: 5000 });
    await expect(popup.getByTestId("wp-words")).toBeVisible();
    await expect(popup.getByTestId("wp-chip")).toHaveCount(2);
    await popup.getByTestId("wp-chip").filter({ hasText: "Zqxhund" }).click();
    await expect(popup.getByTestId("wp-translation")).toHaveText("zqxit");
    await popup.getByTestId("wp-close").click();
    // "pause on click" can be switched off: the film keeps playing under the card
    await openMenu(page);
    await page.getByTestId("sub-pause-on-word").uncheck();
    await closeMenu(page);
    await video(page).evaluate((v: HTMLVideoElement) => { v.currentTime = 0.6; return v.play(); });
    await page.locator('[data-testid="film-cue-line"] [data-word="Zqxhund"]').click();
    await expect(popup).toBeVisible();
    expect(await video(page).evaluate((v: HTMLVideoElement) => v.paused)).toBe(false);
    await popup.getByTestId("wp-close").click();
    await openMenu(page);
    await page.getByTestId("sub-pause-on-word").check();
    await closeMenu(page);
  });

  test("continue watching: position, subtitle language, dual, speed and quality come back", async ({ page }) => {
    test.setTimeout(90_000);
    await studentLogin(page, student);
    await openFilm(page, fx.main);
    await pickSubtitle(page, "uz");
    await openMenu(page);
    await page.getByTestId("sub-dual").check();
    await page.getByTestId("sub-secondary").selectOption("en");
    await closeMenu(page);
    await ctl(page, "film-speed");
    await page.getByTestId("film-speed-option").filter({ hasText: "1.5×" }).click();
    await ctl(page, "film-quality");
    await page.getByTestId("film-quality-option").nth(1).click();
    await expect(video(page)).toHaveAttribute("data-source", /^(?!main$).+/);
    await expect.poll(() => video(page).evaluate((v: HTMLVideoElement) => v.readyState), { timeout: 15_000 }).toBeGreaterThan(1);
    await seek(page, 11.2);
    await page.waitForTimeout(500);
    // leave the page: the position and the choices are stored for this student and film
    await page.goto("/medien/filme");
    const token = await login(student, PASSWORD);
    await expect.poll(async () => (await call("POST", `/medien/films/${fx.main}/watch`, token)).json.progress?.state, { timeout: 15_000 })
      .toMatchObject({ subtitle: "uz", dual: true, secondary: "en", speed: 1.5, quality: "360p" });
    await expect(page.getByTestId("film-continue")).toContainText("B Hauptfilm", { timeout: 20_000 });
    await page.getByTestId("continue-film").first().click();
    await page.waitForTimeout(1200);
    await expect(page.getByTestId("film-player")).toBeVisible({ timeout: 20_000 });
    await expect.poll(() => video(page).evaluate((v: HTMLVideoElement) => v.currentTime), { timeout: 30_000 }).toBeGreaterThan(10.5);
    expect(await video(page).evaluate((v: HTMLVideoElement) => v.playbackRate)).toBe(1.5);
    await expect(page.getByTestId("film-speed")).toHaveText("1.5×");
    await expect(video(page)).toHaveAttribute("data-source", /^(?!main$).+/);
    await video(page).evaluate((v: HTMLVideoElement) => { v.currentTime = 12; v.pause(); });
    await expect.poll(() => lineTexts(page)).toEqual([UZ[3], EN[3]]);
    await openMenu(page);
    await expect(page.getByTestId("sub-dual")).toBeChecked();
    await expect(page.getByTestId("sub-secondary")).toHaveValue("en");
    await closeMenu(page);
    // another student starts from the defaults
    const other = await createStudent();
    const otherToken = await login(other, PASSWORD);
    expect((await call("POST", `/medien/films/${fx.main}/watch`, otherToken)).json.progress).toBeNull();
    // set it back for the next tests
    await pickSubtitle(page, "de");
    await openMenu(page);
    await page.getByTestId("sub-dual").uncheck();
    await closeMenu(page);
  });

  test("access: a paid film has no player, no stream and no subtitle without a purchase; revoking closes the old links", async ({ page }) => {
    test.setTimeout(90_000);
    const buyer = await createStudent();
    const buyerToken = await login(buyer, PASSWORD);
    await loginViaForm(page, buyer, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);
    await page.goto(`/medien/filme/${fx.premium}`);
    await expect(page.getByTestId("film-poster")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByTestId("film-player")).toHaveCount(0);
    expect((await call("POST", `/medien/films/${fx.premium}/watch`, buyerToken)).status).toBe(403);
    // grant (Super Admin) -> the player opens with its subtitles
    await call("POST", "/admin/medien/purchases/grant", adminToken, { kind: "FILM", content_id: fx.premium, email: buyer });
    await page.reload();
    await expect(page.getByTestId("film-player")).toBeVisible({ timeout: 20_000 });
    const watch = (await call("POST", `/medien/films/${fx.premium}/watch`, buyerToken)).json;
    expect(watch.subtitles.map((s: { language: string }) => s.language)).toEqual(["de", "uz"]);
    const urls = [watch.source.url, watch.subtitles[0].cues_url, watch.subtitles[0].url];
    for (const u of urls) expect((await fetch(`${API_URL}${u}`, { headers: { Range: "bytes=0-9" } })).status, u).toBeLessThan(300);
    const ranged = await fetch(`${API_URL}${watch.source.url}`, { headers: { Range: "bytes=0-99" } });
    expect([ranged.status, (await ranged.arrayBuffer()).byteLength]).toEqual([206, 100]);
    // another student cannot use these links either way: their own access decides
    const stranger = await createStudent();
    expect((await call("POST", `/medien/films/${fx.premium}/watch`, await login(stranger, PASSWORD))).status).toBe(403);
    // revoke: the links that were already issued stop working
    const purchases = (await call("GET", "/admin/medien/purchases", adminToken)).json as { id: string; content_id: string; status: string; user_email: string }[];
    const mine = purchases.find((p) => p.content_id === fx.premium && p.status === "GRANTED" && p.user_email === buyer)!;
    await call("POST", `/admin/medien/purchases/${mine.id}/decision`, adminToken, { status: "REVOKED" });
    for (const u of urls) expect((await fetch(`${API_URL}${u}`)).status, u).toBe(403);
    await page.reload();
    await expect(page.getByTestId("film-poster")).toBeVisible({ timeout: 20_000 });
  });
});

test.describe("Film player on a phone", () => {
  test.skip(({ isMobile }) => !isMobile, "phone layout");
  test("the player, its menus and the word card fit the screen and can be used by touch", async ({ page }) => {
    test.setTimeout(180_000);
    const adminToken = await login(ADMIN.email, ADMIN.password);
    const fx = await createFixtures(adminToken);
    try {
      const email = await createStudent();
      await studentLogin(page, email);
      await openFilm(page, fx.main);
      await noHorizontalScroll(page);
      const box = (await page.getByTestId("film-player").boundingBox())!;
      const vw = page.viewportSize()!.width;
      expect(box.x).toBeGreaterThanOrEqual(0);
      expect(box.x + box.width).toBeLessThanOrEqual(vw + 1);
      // the controls bar is reachable: every button is big enough to tap and none is cut off
      await seek(page, 1);
      const buttons = await page.getByTestId("film-controls").locator("button").evaluateAll((els) => els.filter((e) => (e as HTMLElement).offsetParent).map((e) => { const r = e.getBoundingClientRect(); return { w: r.width, h: r.height, right: r.right, left: r.left }; }));
      expect(buttons.length).toBeGreaterThan(8);
      for (const b of buttons) { expect(b.h).toBeGreaterThanOrEqual(43.5); expect(b.w).toBeGreaterThanOrEqual(39); expect(b.left).toBeGreaterThanOrEqual(0); expect(b.right).toBeLessThanOrEqual(vw + 1); }
      // play by touch
      await page.getByTestId("film-play").tap();
      await expect.poll(() => video(page).evaluate((v: HTMLVideoElement) => v.currentTime), { timeout: 20_000 }).toBeGreaterThan(1.5);
      await page.getByTestId("film-play").tap();
      // the subtitle panel stays on screen and scrolls inside itself
      await page.getByTestId("film-subtitles").tap();
      const menu = page.getByTestId("film-subtitle-menu");
      await expect(menu).toBeVisible();
      const m = (await menu.boundingBox())!;
      expect(m.x).toBeGreaterThanOrEqual(0);
      expect(m.x + m.width).toBeLessThanOrEqual(vw + 1);
      expect(m.y).toBeGreaterThanOrEqual(box.y - 1);          // the sheet lies inside the player
      expect(m.y + m.height).toBeLessThanOrEqual(box.y + box.height + 1);
      await page.getByTestId("sub-dual").check();
      await page.getByTestId("sub-size-large").tap();
      await page.getByTestId("film-menu-close").tap();      // the sheet has its own close button
      await expect(menu).toHaveCount(0);
      await seek(page, 1);
      await expect.poll(() => lineTexts(page)).toEqual([DE[0], UZ[0]]);
      const cue = (await page.getByTestId("film-cue").boundingBox())!;
      expect(cue.x).toBeGreaterThanOrEqual(0);
      expect(cue.x + cue.width).toBeLessThanOrEqual(vw + 1);
      await noHorizontalScroll(page);
      // tap a German word: the card opens as a sheet inside the screen; the close button works
      await page.locator('[data-testid="film-cue-line"][data-language="de"] [data-word="Zqxhund"]').tap();
      const popup = page.getByTestId("word-popup");
      await expect(popup).toBeVisible();
      await expect(popup.getByTestId("wp-translation")).toHaveText("zqxit");
      const p = (await popup.boundingBox())!;
      expect(p.x).toBeGreaterThanOrEqual(0);
      expect(p.x + p.width).toBeLessThanOrEqual(vw + 1);
      expect(p.y).toBeGreaterThanOrEqual(0);
      await popup.getByTestId("wp-close").tap();
      await expect(popup).toHaveCount(0);
      await noHorizontalScroll(page);
      await page.screenshot({ path: "test-results/film-player-phone.png" });
    } finally {
      await removeFixtures(fx);
    }
  });
});
