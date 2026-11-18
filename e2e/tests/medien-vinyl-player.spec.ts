import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { expect, test, type Page } from "@playwright/test";

import { ADMIN, API_URL, PASSWORD, createStudent, loginViaForm } from "./helpers";

// Medien → Musik vinyl player (local stack, needs ffmpeg = FFMPEG_BIN): the large vinyl player opens on Play, the disc turns and stops
// with the music; on every other page the SAME <audio> keeps playing and a floating vinyl disc with a small panel appears; back on Musik
// the disc goes away and the song goes on (no restart); X stops the music for good; a reload brings the song back (paused) at its position;
// a film / exam audio that starts pauses the music; Media Session metadata; phone layout. Real Android background playback is a device check.
const FFMPEG = process.env.FFMPEG_BIN ?? "ffmpeg";
const TAG = `V${Date.now().toString(36)}${Math.random().toString(36).slice(2, 5)}`;
const work = mkdtempSync(join(tmpdir(), "vinyl-"));
const SILENT = "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABAAZGF0YQAAAAA=";

function ffmpeg(args: string[]) { execFileSync(FFMPEG, ["-nostdin", "-v", "error", "-y", ...args], { stdio: "pipe" }); }

async function token(email: string, password: string) {
  const res = await fetch(`${API_URL}/api/v1/auth/login`, { method: "POST", headers: { "Content-Type": "application/json", "X-Forwarded-For": `10.97.${Math.floor(Math.random() * 250)}.${Math.floor(Math.random() * 250)}` }, body: JSON.stringify({ identifier: email, password }) });
  expect(res.status, await res.clone().text()).toBe(200);
  return (await res.json()).access_token as string;
}

async function studentLogin(page: Page, email: string) {
  await loginViaForm(page, email, PASSWORD);
  await expect(page).toHaveURL(/\/dashboard/);
  await page.evaluate(() => localStorage.setItem("vizu-language", JSON.stringify({ state: { language: "uz" }, version: 0 })));
  await page.reload();
}

const audio = (page: Page) => page.evaluate(() => { const a = document.querySelector('[data-testid="global-audio"]') as HTMLAudioElement; return { paused: a.paused, t: a.currentTime, volume: a.volume, muted: a.muted, src: a.getAttribute("src"), count: document.querySelectorAll("audio").length }; });
const sameElement = (page: Page) => page.evaluate(() => (window as unknown as { __audio: Element }).__audio === document.querySelector('[data-testid="global-audio"]'));

/** the disc's real turning: the animation state AND the angle moving over time */
async function spin(page: Page, selector: string) {
  const read = () => page.evaluate((sel) => { const el = document.querySelector(`${sel} [data-role="vinyl-spin"]`) as HTMLElement; const cs = getComputedStyle(el); return { state: cs.animationPlayState, transform: cs.transform }; }, selector);
  const a = await read();
  await page.waitForTimeout(450);
  const b = await read();
  return { state: b.state, moved: a.transform !== b.transform };
}

/** client-side navigation through a real link of the page (no reload) */
async function go(page: Page, href: string) {
  const found = await page.evaluate((h) => { const a = Array.from(document.querySelectorAll("a")).find((x) => x.getAttribute("href") === h) as HTMLAnchorElement | undefined; a?.click(); return !!a; }, href);
  expect(found, `no link to ${href} on ${page.url()}`).toBe(true);
  await expect(page).toHaveURL(new RegExp(`${href.replace(/\//g, "\\/")}$`));
  await page.waitForTimeout(1200); // PageTransition settles
}

async function startOnMusik(page: Page, row = 0) {
  await page.goto("/medien/musik");
  await expect(async () => { await page.getByTestId("song-search").fill(TAG); await expect(page.getByTestId("song-row")).toHaveCount(3, { timeout: 3000 }); }).toPass({ timeout: 20_000 });
  // the search list is sorted by popularity: songs with the same count may swap places on a refetch (even under the pointer), so the
  // song is followed by its title and the click is repeated until that song is the one playing
  const title = `${TAG}-${["a", "b", "c"][row]}`;
  await expect(async () => {
    if (await page.getByTestId("vinyl-player").count()) await page.getByTestId("vinyl-minimize").click();
    await page.getByTestId("song-row").filter({ hasText: title }).first().getByTestId("song-play").click();
    await expect(page.getByTestId("vinyl-title")).toHaveText(title, { timeout: 2500 });
  }).toPass({ timeout: 25_000 });
  await expect(page.getByTestId("vinyl-player")).toBeVisible();
  await expect.poll(async () => (await audio(page)).t, { timeout: 20_000 }).toBeGreaterThan(0.8);
  await page.evaluate(() => { (window as unknown as { __audio: Element }).__audio = document.querySelector('[data-testid="global-audio"]')!; });
  return title;
}

/** next / previous follow the queue the player saved (the list order when Play was pressed); "previous" on the first song restarts it */
async function nextAndBack(page: Page, nextBtn: string, prevBtn: string, titleId: string) {
  const q = await page.evaluate(() => { const v = JSON.parse(localStorage.getItem("vizu-player-v1") ?? "null"); return v ? { titles: (v.queue as { title: string }[]).map((s) => s.title), index: v.index as number } : null; });
  expect(q).not.toBeNull();
  const nextIdx = q!.index + 1 < q!.titles.length ? q!.index + 1 : 0;
  await page.getByTestId(nextBtn).click();
  await expect(page.getByTestId(titleId)).toHaveText(q!.titles[nextIdx]);
  await expect.poll(async () => (await audio(page)).t, { timeout: 15_000 }).toBeGreaterThan(0.3);
  await page.getByTestId(prevBtn).click(); // within 3 s: the song before (on the first one: from its start)
  await expect(page.getByTestId(titleId)).toHaveText(nextIdx === 0 ? q!.titles[0] : q!.titles[nextIdx - 1]);
}

test.use({ launchOptions: { args: ["--autoplay-policy=no-user-gesture-required"] } });

let admin = "";
const songIds: string[] = [];

test.beforeAll(async () => {
  admin = await token(ADMIN.email, ADMIN.password);
  ffmpeg(["-f", "lavfi", "-i", "testsrc=size=400x400:rate=1", "-frames:v", "1", join(work, "cover.png")]);
  for (const [i, name] of ["a", "b", "c"].entries()) {
    const path = join(work, `${TAG}-${name}.mp3`);
    ffmpeg(["-f", "lavfi", "-i", `sine=frequency=${330 + i * 110}:duration=40`, "-c:a", "libmp3lame", path]);
    const form = new FormData();
    form.append("file", new Blob([readFileSync(path)], { type: "audio/mpeg" }), `${TAG}-${name}.mp3`);
    if (i < 2) form.append("cover", new Blob([readFileSync(join(work, "cover.png"))], { type: "image/png" }), "cover.png");
    form.append("title", `${TAG}-${name}`); form.append("artist", "Vinyl Band"); form.append("status", "PUBLISHED");
    const made = await fetch(`${API_URL}/api/v1/admin/medien/songs`, { method: "POST", headers: { Authorization: `Bearer ${admin}` }, body: form });
    expect(made.status, await made.clone().text()).toBe(200);
    songIds.push((await made.json()).id as string);
  }
});

test.afterAll(async () => {
  for (const id of songIds) await fetch(`${API_URL}/api/v1/admin/medien/songs/${id}`, { method: "DELETE", headers: { Authorization: `Bearer ${admin}` } });
  rmSync(work, { recursive: true, force: true });
});

test.describe.serial("vinyl player (desktop)", () => {
  test.skip(({ isMobile }) => isMobile, "desktop; the phone layout has its own test");
  let student = "";
  test.beforeAll(async () => { student = await createStudent(); });

  test("Play on Musik opens the large vinyl player; the disc turns, stops on pause, turns again on play; controls", async ({ page }) => {
    await studentLogin(page, student);
    const title = await startOnMusik(page);
    const player = page.getByTestId("vinyl-player");
    await expect(player.getByTestId("vinyl-title")).toHaveText(title);
    await expect(player.getByTestId("vinyl-artist")).toContainText("Vinyl Band");
    await expect(player.getByTestId("vinyl-duration")).toHaveText("0:40");
    await expect(page.getByTestId("player-bar")).toHaveCount(0); // the large player is the view now
    await expect(page.getByTestId("floating-vinyl")).toHaveCount(0);
    expect(await spin(page, '[data-testid="vinyl-disc"]')).toEqual({ state: "running", moved: true });
    await expect(player.getByTestId("vinyl-arm")).toHaveAttribute("data-down", "1");
    await page.screenshot({ path: "test-results/vinyl-large-desktop.png" });

    await player.getByTestId("vinyl-play").click(); // pause
    await expect.poll(async () => (await audio(page)).paused).toBe(true);
    expect(await spin(page, '[data-testid="vinyl-disc"]')).toEqual({ state: "paused", moved: false });
    await expect(player.getByTestId("vinyl-arm")).toHaveAttribute("data-down", "0");
    await player.getByTestId("vinyl-play").click(); // play
    await expect.poll(async () => (await audio(page)).paused).toBe(false);
    expect(await spin(page, '[data-testid="vinyl-disc"]')).toEqual({ state: "running", moved: true });

    await player.getByTestId("vinyl-progress").fill("12");
    await expect.poll(async () => (await audio(page)).t).toBeGreaterThan(11.5);
    await player.getByTestId("vinyl-volume").fill("0.4");
    expect((await audio(page)).volume).toBeCloseTo(0.4, 1);
    await player.getByTestId("vinyl-mute").click();
    expect((await audio(page)).muted).toBe(true);
    await player.getByTestId("vinyl-mute").click();
    await nextAndBack(page, "vinyl-next", "vinyl-prev", "vinyl-title");
    // lock screen / headset: the Media Session knows the song and its cover
    const now = (await player.getByTestId("vinyl-title").textContent())!;
    const meta = await page.evaluate(() => ({ title: navigator.mediaSession.metadata?.title, artist: navigator.mediaSession.metadata?.artist, art: navigator.mediaSession.metadata?.artwork.length, state: navigator.mediaSession.playbackState }));
    expect(meta).toEqual({ title: now, artist: "Vinyl Band", art: now.endsWith("-c") ? 0 : 4, state: "playing" }); // -c has no cover
    expect((await audio(page)).count).toBe(1); // one audio element only

    await player.getByTestId("vinyl-minimize").click(); // closes the window, the music goes on
    await expect(player).toHaveCount(0);
    await expect(page.getByTestId("player-bar")).toBeVisible();
    expect((await audio(page)).paused).toBe(false);
    await page.getByTestId("player-open-large").click(); // the bar reopens it
    await expect(page.getByTestId("vinyl-player")).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.getByTestId("vinyl-player")).toHaveCount(0);
  });

  test("other pages: same audio keeps playing, floating disc + panel; back on Musik: no disc, no restart", async ({ page }) => {
    await studentLogin(page, student);
    const title = await startOnMusik(page);
    await page.getByTestId("vinyl-minimize").click();
    const pages = ["/dashboard", "/vorbereitung", "/medien", "/medien/bibliothek", "/medien", "/medien/filme"];
    for (const href of pages) {
      const before = (await audio(page)).t;
      await go(page, href);
      expect(await sameElement(page), `audio element recreated on ${href}`).toBe(true);
      const now = await audio(page);
      expect(now.paused, `paused on ${href}`).toBe(false);
      expect(now.t).toBeGreaterThan(before);
      await expect(page.getByTestId("floating-vinyl")).toBeVisible();
      await expect(page.getByTestId("player-bar")).toHaveCount(0);
      await expect(page.getByTestId("vinyl-player")).toHaveCount(0);
      expect((await spin(page, '[data-testid="floating-vinyl"]')).state).toBe("running");
    }
    await page.screenshot({ path: "test-results/vinyl-floating-desktop.png" });

    // the panel: title, artist, progress, play / pause, next / previous, outside tap closes it
    await page.getByTestId("floating-disc").click();
    const panel = page.getByTestId("floating-panel");
    await expect(panel.getByTestId("floating-title")).toHaveText(title);
    await expect(panel.getByTestId("floating-artist")).toHaveText("Vinyl Band");
    await page.screenshot({ path: "test-results/vinyl-panel-desktop.png" });
    await panel.getByTestId("floating-play").click();
    await expect.poll(async () => (await audio(page)).paused).toBe(true);
    expect(await spin(page, '[data-testid="floating-vinyl"] [data-testid="floating-disc-art"]')).toEqual({ state: "paused", moved: false });
    await panel.getByTestId("floating-play").click();
    await expect.poll(async () => (await audio(page)).paused).toBe(false);
    await nextAndBack(page, "floating-next", "floating-prev", "floating-title");
    const shown = (await panel.getByTestId("floating-title").textContent())!;
    await panel.getByTestId("floating-progress").fill("9");
    await expect.poll(async () => (await audio(page)).t).toBeGreaterThan(8.5);
    await page.mouse.click(30, 300); // outside
    await expect(panel).toHaveCount(0);
    // the large player opens on any page and goes away again with the music still on
    await page.getByTestId("floating-disc").click();
    await page.getByTestId("floating-expand").click();
    await expect(page.getByTestId("vinyl-player")).toBeVisible();
    await expect(page.getByTestId("floating-vinyl")).toHaveCount(0);
    await page.getByTestId("vinyl-minimize").click();
    await expect(page.getByTestId("floating-vinyl")).toBeVisible();

    // back to Musik: the disc disappears, the normal page shows, the song goes on from where it is
    const before = (await audio(page)).t;
    await go(page, "/medien");
    await page.getByTestId("medien-card-music").click();
    await expect(page).toHaveURL(/\/medien\/musik$/);
    await page.waitForTimeout(1200);
    await expect(page.getByTestId("floating-vinyl")).toHaveCount(0);
    await expect(page.getByTestId("vinyl-player")).toHaveCount(0);
    await expect(page.getByTestId("musik")).toBeVisible();
    await expect(page.getByTestId("player-bar")).toBeVisible();
    await expect(page.getByTestId("player-title")).toHaveText(shown);
    expect(await sameElement(page)).toBe(true);
    const after = await audio(page);
    expect(after.paused).toBe(false);
    expect(after.t).toBeGreaterThan(before); // no restart
  });

  test("one sound at a time: another audio that starts pauses the music", async ({ page }) => {
    await studentLogin(page, student);
    await startOnMusik(page);
    await page.getByTestId("vinyl-minimize").click();
    await go(page, "/dashboard");
    await page.evaluate((src) => { const a = document.createElement("audio"); a.id = "other"; a.src = src; document.body.appendChild(a); void a.play(); }, SILENT);
    await expect.poll(async () => (await audio(page)).paused).toBe(true);
    await expect(page.getByTestId("floating-vinyl")).toHaveAttribute("data-playing", "0");
    await page.evaluate(() => document.getElementById("other")?.remove());
  });

  test("reload restores the song (paused) at its position; X stops the music for good", async ({ page }) => {
    await studentLogin(page, student);
    const title = await startOnMusik(page, 1);
    await page.getByTestId("vinyl-progress").fill("15");
    await expect.poll(async () => (await audio(page)).t).toBeGreaterThan(14.5);
    await page.getByTestId("vinyl-minimize").click();
    await go(page, "/dashboard");
    await page.waitForTimeout(4500); // saved every few seconds while playing
    await page.reload();
    await expect(page.getByTestId("floating-vinyl")).toBeVisible();
    await expect(page.getByTestId("floating-vinyl")).toHaveAttribute("data-playing", "0");
    expect((await audio(page)).paused).toBe(true);
    await page.getByTestId("floating-disc").click();
    await expect(page.getByTestId("floating-title")).toHaveText(title);
    await expect(page.getByTestId("floating-time")).not.toHaveText("0:00");
    await page.getByTestId("floating-play").click();
    await expect.poll(async () => (await audio(page)).t, { timeout: 20_000 }).toBeGreaterThan(14);
    expect((await audio(page)).paused).toBe(false);

    // X: the audio really stops, the player is emptied, nothing comes back after a reload
    await page.getByTestId("floating-close").click();
    await expect(page.getByTestId("floating-vinyl")).toHaveCount(0);
    const stopped = await audio(page);
    expect([stopped.paused, stopped.src]).toEqual([true, null]);
    expect(await page.evaluate(() => localStorage.getItem("vizu-player-v1"))).toBeNull();
    await page.reload();
    await expect(page.locator("main")).toBeVisible();
    await page.waitForTimeout(800);
    await expect(page.getByTestId("floating-vinyl")).toHaveCount(0);
    await page.goto("/medien/musik");
    await expect(page.getByTestId("musik")).toBeVisible();
    await expect(page.getByTestId("player-bar")).toHaveCount(0);

    // X in the large player does the same
    await startOnMusik(page);
    await page.getByTestId("vinyl-close").click();
    await expect(page.getByTestId("vinyl-player")).toHaveCount(0);
    await expect(page.getByTestId("player-bar")).toHaveCount(0);
    const again = await audio(page);
    expect([again.paused, again.src]).toEqual([true, null]);
  });
});

test("phone: large player fills the screen, floating disc sits above the chat button, panel fits and has touch-size buttons", async ({ page, isMobile }) => {
  test.skip(!isMobile, "phone layout");
  const student = await createStudent();
  await studentLogin(page, student);
  await startOnMusik(page);
  const vp = page.viewportSize()!;
  const box = (await page.getByTestId("vinyl-player").boundingBox())!;
  expect(Math.round(box.width)).toBe(vp.width);
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
  expect((await spin(page, '[data-testid="vinyl-disc"]')).state).toBe("running");
  await page.screenshot({ path: "test-results/vinyl-large-phone.png" });
  await page.getByTestId("vinyl-minimize").click();
  await go(page, "/medien");
  const disc = (await page.getByTestId("floating-disc").boundingBox())!;
  const chat = (await page.getByTestId("global-chat-button").boundingBox())!;
  expect(disc.x + disc.width).toBeLessThanOrEqual(vp.width - 8); // a margin to the edge
  expect(disc.y + disc.height).toBeLessThanOrEqual(chat.y - 4); // above the chat button, no overlap
  expect(disc.width).toBeGreaterThanOrEqual(44);
  await page.getByTestId("floating-disc").click();
  const panel = (await page.getByTestId("floating-panel").boundingBox())!;
  expect(panel.x).toBeGreaterThanOrEqual(0);
  expect(panel.x + panel.width).toBeLessThanOrEqual(vp.width);
  for (const id of ["floating-prev", "floating-play", "floating-next", "floating-close", "floating-expand"]) {
    const b = (await page.getByTestId(id).boundingBox())!;
    expect(Math.min(b.width, b.height), id).toBeGreaterThanOrEqual(43.5);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
  await page.screenshot({ path: "test-results/vinyl-floating-phone.png" });
  await page.getByTestId("floating-close").click();
  await expect(page.getByTestId("floating-vinyl")).toHaveCount(0);
  expect((await audio(page)).paused).toBe(true);
});
