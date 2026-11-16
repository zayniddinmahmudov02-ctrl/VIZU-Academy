import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { expect, test, type Page } from "@playwright/test";

import { ADMIN, API_URL, PASSWORD, createStudent, loginViaForm } from "./helpers";

// Admin → Medien → Musik: every supported audio format (MP3, WAV, M4A, AAC, OGG, FLAC) in one bulk upload, read by the server (format, duration, bitrate, tags), one broken
// file that must not stop the others — and the student's player really plays a lossless file. Needs ffmpeg (FFMPEG_BIN) like medien.spec.ts. Local stack only.
const FFMPEG = process.env.FFMPEG_BIN ?? "ffmpeg";
const TAG = `M${Date.now().toString(36)}${Math.random().toString(36).slice(2, 5)}`;
const work = mkdtempSync(join(tmpdir(), "music-formats-"));
const FORMATS: [string, string, string[]][] = [
  ["mp3", "audio/mpeg", ["-c:a", "libmp3lame", "-b:a", "128k"]],
  ["wav", "audio/wav", ["-c:a", "pcm_s16le"]],
  ["m4a", "audio/mp4", ["-c:a", "aac", "-b:a", "96k"]],
  ["aac", "audio/aac", ["-c:a", "aac", "-b:a", "96k", "-f", "adts"]],
  ["ogg", "audio/ogg", ["-c:a", "libvorbis"]],
  ["flac", "audio/flac", ["-c:a", "flac"]],
];

function make(ext: string, codec: string[], seconds = 6) {
  const path = join(work, `${TAG}-${ext}.${ext}`);
  execFileSync(FFMPEG, ["-nostdin", "-v", "error", "-y", "-f", "lavfi", "-i", `sine=frequency=${300 + ext.length * 70}:duration=${seconds}`, ...codec, "-metadata", `artist=Tag Band ${ext}`, path], { stdio: "pipe" });
  return path;
}

async function token(email: string, password: string) {
  const res = await fetch(`${API_URL}/api/v1/auth/login`, { method: "POST", headers: { "Content-Type": "application/json", "X-Forwarded-For": `10.95.${Math.floor(Math.random() * 250)}.${Math.floor(Math.random() * 250)}` }, body: JSON.stringify({ identifier: email, password }) });
  expect(res.status, await res.clone().text()).toBe(200);
  return (await res.json()).access_token as string;
}

async function adminLogin(page: Page) {
  await page.addInitScript(() => localStorage.setItem("vizu-language", JSON.stringify({ state: { language: "de" }, version: 0 })));
  await loginViaForm(page, ADMIN.email, ADMIN.password);
  await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
  await page.getByRole("button", { name: "Bestätigen" }).click();
  await expect(page).toHaveURL(/\/admin/);
}

test.use({ launchOptions: { args: ["--autoplay-policy=no-user-gesture-required"] } });

test.describe.serial("Musik: all audio formats", () => {
  test.skip(({ isMobile }) => isMobile, "desktop");
  let admin = "";
  const ids: string[] = [];

  test.beforeAll(async () => { admin = await token(ADMIN.email, ADMIN.password); });
  test.afterAll(async () => {
    const list = await fetch(`${API_URL}/api/v1/admin/medien/songs?q=${TAG}&page_size=50`, { headers: { Authorization: `Bearer ${admin}` } });
    for (const s of ((await list.json()).items ?? []) as { id: string }[]) await fetch(`${API_URL}/api/v1/admin/medien/songs/${s.id}`, { method: "DELETE", headers: { Authorization: `Bearer ${admin}` } });
    void ids;
    rmSync(work, { recursive: true, force: true });
  });

  test("admin: bulk upload of MP3, WAV, M4A, AAC, OGG, FLAC and a broken file — each read by the server, the broken one refused, the rest unaffected", async ({ page }) => {
    await adminLogin(page);
    await page.goto("/admin/medien/musik");
    const files = FORMATS.map(([ext, type, codec]) => ({ name: `${TAG}-${ext}.${ext}`, mimeType: type, buffer: readFileSync(make(ext, codec)) }));
    files.splice(3, 0, { name: `${TAG}-kaputt.mp3`, mimeType: "audio/mpeg", buffer: Buffer.from("das ist keine audiodatei") });
    await page.getByTestId("bulk-file").setInputFiles(files);
    await expect(page.getByTestId("bulk-row")).toHaveCount(7);
    await page.getByTestId("bulk-start").click();
    await expect(page.getByTestId("bulk-summary")).toContainText("6 hochgeladen", { timeout: 120_000 });
    await expect(page.getByTestId("bulk-summary")).toContainText("1 mit Fehler");
    await expect(page.locator('[data-testid="bulk-row"][data-state="error"]')).toHaveCount(1);
    for (const [ext] of FORMATS) {
      const row = page.locator(`[data-testid="bulk-row"][data-file="${TAG}-${ext}.${ext}"]`);
      await expect(row).toHaveAttribute("data-state", "done");
      await expect(row.getByTestId("bulk-info")).toContainText(ext.toUpperCase()); // "WAV · 0:06 · 705 kbps · 0.5 MB"
      await expect(row.getByTestId("bulk-info")).toContainText("0:06");
      await expect(row.getByTestId("bulk-warn")).toHaveCount(0); // metadata was read
    }
    // the list shows format and bitrate, the tags filled the artist the admin left empty
    await page.getByTestId("songs-search").fill(TAG);
    await expect(page.getByTestId("song-admin-row")).toHaveCount(6);
    const wav = page.locator(`[data-testid="song-admin-row"][data-title="${TAG}-wav"]`);
    await expect(wav.getByTestId("song-format")).toContainText("WAV");
    await expect(wav).toContainText("0:06");
    await expect(wav).toContainText("Tag Band wav");
    await expect(page.getByTestId("song-meta-failed")).toHaveCount(0);
    // an admin can still change everything the server read
    await wav.getByTestId("song-edit").click();
    await page.getByTestId("song-dialog").getByTestId("f-title").fill(`${TAG}-wav neu`);
    await page.getByTestId("song-save").click();
    await expect(page.getByTestId("song-note")).toHaveText("Gespeichert.");
  });

  test("student: the player plays a WAV and a FLAC, keeps playing on another page", async ({ page }) => {
    const student = await createStudent();
    await loginViaForm(page, student, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);
    await page.evaluate(() => localStorage.setItem("vizu-language", JSON.stringify({ state: { language: "uz" }, version: 0 })));
    await page.goto("/medien/musik");
    await page.getByTestId("song-search").fill(`${TAG}-flac`);
    await expect(page.getByTestId("song-row")).toHaveCount(1);
    await page.getByTestId("song-play").first().click();
    await expect(page.getByTestId("player-bar")).toBeVisible();
    await expect.poll(() => page.evaluate(() => (document.querySelector("audio") as HTMLAudioElement).currentTime), { timeout: 20_000 }).toBeGreaterThan(0.8);
    expect(await page.evaluate(() => (document.querySelector("audio") as HTMLAudioElement).duration)).toBeGreaterThan(5.5);
    await page.getByTestId("song-search").fill(`${TAG}-wav`);
    await expect(page.getByTestId("song-row").first()).toContainText(`${TAG}-wav`); // the list follows the (debounced) search
    await page.getByTestId("song-play").first().click();
    await expect(page.getByTestId("player-title")).toContainText(`${TAG}-wav`);
    await expect.poll(() => page.evaluate(() => { const a = document.querySelector("audio") as HTMLAudioElement; return !a.paused && a.currentTime > 0.8; }), { timeout: 20_000 }).toBe(true);
    // background playback: client-side navigation, the same audio element keeps running
    await page.evaluate(() => { (window as unknown as { __audio: Element }).__audio = document.querySelector('[data-testid="global-audio"]')!; });
    const before = await page.evaluate(() => (document.querySelector("audio") as HTMLAudioElement).currentTime);
    await page.locator('aside a[href="/kurse"]').first().click();
    await expect(page).toHaveURL(/\/kurse/);
    await page.waitForTimeout(1500);
    const state = await page.evaluate(() => { const a = document.querySelector("audio") as HTMLAudioElement; return { paused: a.paused, t: a.currentTime, same: (window as unknown as { __audio: Element }).__audio === document.querySelector('[data-testid="global-audio"]') }; });
    expect(state.same).toBe(true); // the very same audio element: no restart
    expect(state.paused).toBe(false);
    expect(state.t).toBeGreaterThan(before);
  });
});
