import { expect, test, type Locator, type Page } from "@playwright/test";

import { API_URL, apiToken, loginViaForm, useLanguage } from "./helpers";

/** Group video lesson, end to end against a REAL local LiveKit server (D:\vz_tmp\livekit, see docs/group-video-lessons.md):
 * teacher and student in two browser contexts with Chrome's fake camera / microphone see and hear each other, mute,
 * camera off, chat, raise hand, teacher moderation, screen share, leave, end. Seed: D:\vz_tmp\work\video_e2e_seed.py.
 * Not covered here (needs real devices / networks): real cameras, UDP-blocked networks, TURN fallback. */

const PASSWORD = "Geheim123!";
const TEACHER = "vr-teacher@example.com";
const STUDENT = "vr-student1@example.com";
const OUTSIDER = "vr-outsider@example.com";
const GROUP = "E2E Video Gruppe";
const FAKE_MEDIA = ["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "--auto-select-desktop-capture-source=Entire screen",
  "--autoplay-policy=no-user-gesture-required"];

test.use({ launchOptions: { args: FAKE_MEDIA }, permissions: ["camera", "microphone"] });
test.describe.configure({ mode: "serial" });

async function me(email: string): Promise<{ id: string; token: string }> {
  const token = await apiToken(email, PASSWORD);
  const res = await fetch(`${API_URL}/api/v1/users/me`, { headers: { Authorization: `Bearer ${token}` } });
  return { id: (await res.json()).id as string, token };
}

async function groupId(token: string): Promise<string> {
  const res = await fetch(`${API_URL}/api/v1/groups/teaching?page_size=100`, { headers: { Authorization: `Bearer ${token}` } });
  const g = (await res.json()).items.find((x: { name: string }) => x.name === GROUP);
  expect(g, "seed the E2E database first (video_e2e_seed.py)").toBeTruthy();
  return g.id as string;
}

async function login(page: Page, email: string) {
  await loginViaForm(page, email, PASSWORD); // the helper fills the German form
  await page.waitForURL((u) => !u.pathname.startsWith("/login"), { timeout: 20_000 });
  await useLanguage(page, "uz"); // every later page in Uzbek
}

/** A control of the bottom bar; on a phone the secondary ones sit in "More". */
async function control(page: Page, testId: string): Promise<Locator> {
  const visible = page.getByTestId(testId).locator("visible=true");
  if (await visible.count()) return visible.first();
  await page.getByTestId("ctl-more").click();
  return page.getByTestId(testId).locator("visible=true").first();
}

const tile = (page: Page, identity: string, source = "camera") => page.locator(`[data-testid="video-tile"][data-identity="${identity}"][data-source="${source}"]`);

async function videoPlaying(page: Page, identity: string, source = "camera") {
  await expect.poll(() => tile(page, identity, source).locator("video").evaluate((v: HTMLVideoElement) => v.videoWidth).catch(() => 0),
    { timeout: 25_000 }).toBeGreaterThan(0);
}

/** Peak sample level (0..1) of the remote audio over ~3 s, measured with Web Audio on the received MediaStream. */
async function remotePeak(): Promise<number> {
  const el = [...document.querySelectorAll("audio")].find((a) => a.srcObject instanceof MediaStream && a.srcObject.getAudioTracks().length);
  if (!el) return 0;
  const ctx = new AudioContext();
  await ctx.resume();
  const analyser = ctx.createAnalyser();
  analyser.fftSize = 2048;
  ctx.createMediaStreamSource(el.srcObject as MediaStream).connect(analyser);
  const buf = new Float32Array(analyser.fftSize);
  let peak = 0;
  const end = performance.now() + 3000;
  while (performance.now() < end) {
    analyser.getFloatTimeDomainData(buf);
    for (const v of buf) peak = Math.max(peak, Math.abs(v));
    await new Promise((r) => setTimeout(r, 50));
  }
  await ctx.close();
  return peak;
}

async function joinFromPrejoin(page: Page) {
  await expect(page.getByTestId("prejoin")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByTestId("prejoin-preview")).toBeVisible({ timeout: 15_000 });
  await page.getByTestId("video-join").click();
  await expect(page.getByTestId("meeting")).toBeVisible({ timeout: 20_000 });
}

test("teacher and student: see and hear each other, mute, camera, chat, hand, moderation, screen share, leave, end", async ({ page, browser }, info) => {
  test.setTimeout(240_000);
  const teacher = await me(TEACHER);
  const student = await me(STUDENT);
  const gid = await groupId(teacher.token);
  page.on("dialog", (d) => void d.accept());

  // teacher creates and starts the lesson from the group page
  await login(page, TEACHER);
  await page.goto(`/teacher/groups/${gid}?tab=video`);
  await page.getByTestId("video-title").fill(`E2E jonli dars ${info.project.name}`);
  await page.getByTestId("video-description").fill("Perfekt bilan gaplar");
  await page.getByTestId("video-create").click();
  await page.waitForURL(/\/video-room\//, { timeout: 20_000 });
  const roomUrl = page.url();
  await joinFromPrejoin(page);
  await expect(page.getByTestId("meeting-title")).toContainText("E2E jonli dars");

  // student sees the live banner in the group and joins
  const sctx = await browser.newContext({ permissions: ["camera", "microphone"], viewport: { width: 1280, height: 800 } });
  const s = await sctx.newPage();
  s.on("dialog", (d) => void d.accept());
  await login(s, STUDENT);
  await s.goto(`/groups/${gid}`);
  await expect(s.getByTestId("video-live-banner")).toBeVisible({ timeout: 25_000 });
  await s.getByTestId("video-live-join").click();
  await s.waitForURL(/\/video-room\//);
  await joinFromPrejoin(s);

  // both see both videos (frames arrive through the SFU) and hear each other (remote audio tracks are live)
  await videoPlaying(page, student.id);
  await videoPlaying(s, teacher.id);
  await expect(page.getByTestId("meeting-count")).toContainText("2");
  for (const p of [page, s]) {
    await expect.poll(() => p.evaluate(() => [...document.querySelectorAll("audio")].some((a) =>
      a.srcObject instanceof MediaStream && a.srcObject.getAudioTracks().some((tr) => tr.readyState === "live"))), { timeout: 20_000 }).toBe(true);
    // the received audio really carries sound (Chrome's fake microphone beeps): peak level of the remote stream
    await expect.poll(() => p.evaluate(remotePeak), { timeout: 30_000 }).toBeGreaterThan(0.01);
  }

  // student mutes / unmutes; the teacher sees it
  await s.getByTestId("ctl-mic").click();
  await expect(tile(page, student.id).getByLabel("mic off")).toBeVisible({ timeout: 15_000 });
  await s.getByTestId("ctl-mic").click();
  await expect(tile(page, student.id).getByLabel("mic off")).toHaveCount(0, { timeout: 15_000 });

  // camera off / on
  await s.getByTestId("ctl-camera").click();
  await expect(tile(page, student.id).locator("video")).toHaveCount(0, { timeout: 15_000 });
  await s.getByTestId("ctl-camera").click();
  await videoPlaying(page, student.id);

  // teacher mutes the student from the participant list; the student is told
  await (await control(page, "ctl-participants")).click();
  const row = page.locator(`[data-testid="participant-row"][data-identity="${student.id}"]`);
  await row.getByTestId("participant-actions").click();
  await page.getByTestId("action-mute").click();
  await expect(s.getByTestId("meeting-toast").filter({ hasText: "mikrofoningizni" })).toBeVisible({ timeout: 15_000 });
  await expect(tile(page, student.id).getByLabel("mic off")).toBeVisible({ timeout: 15_000 });

  // chat: student writes, teacher reads; then the teacher turns chat off for students
  await s.getByTestId("ctl-chat").click();
  await s.getByTestId("meeting-chat-input").fill("Salom, ustoz!");
  await s.getByTestId("meeting-chat-send").click();
  await page.getByTestId("ctl-chat").click();
  await expect(page.getByTestId("meeting-chat-message").filter({ hasText: "Salom, ustoz!" })).toBeVisible({ timeout: 15_000 });
  await (await control(page, "ctl-participants")).click();
  await page.getByTestId("teacher-chat-all").click();
  await expect(s.getByTestId("meeting-chat-disabled")).toBeVisible({ timeout: 15_000 });

  // raise hand: the teacher sees it and lowers it
  await s.getByTestId("ctl-hand").click();
  await expect(tile(page, student.id).getByTestId("tile-hand")).toBeVisible({ timeout: 15_000 });
  await (await control(page, "ctl-hands")).click();
  await expect(page.getByTestId("hand-row")).toHaveCount(1);
  await page.getByTestId("hand-lower").click();
  await expect(tile(page, student.id).getByTestId("tile-hand")).toHaveCount(0, { timeout: 15_000 });
  await expect(s.getByTestId("meeting-toast").filter({ hasText: "Qo'lingiz tushirildi" })).toBeVisible({ timeout: 10_000 });
  await expect(page.getByTestId("meeting-toast").filter({ hasText: "Qo'lingiz tushirildi" })).toHaveCount(0); // never for the teacher

  // teacher shares the screen; the student sees it large
  await (await control(page, "ctl-screen")).click();
  await videoPlaying(s, teacher.id, "screen_share");
  await expect(s.getByTestId("video-grid")).toHaveAttribute("data-layout", "speaker");
  await (await control(page, "ctl-screen")).click();
  await expect(tile(s, teacher.id, "screen_share")).toHaveCount(0, { timeout: 15_000 });

  // no horizontal scroll in the meeting
  for (const p of [page, s]) expect(await p.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1);

  // student leaves; the teacher is alone
  await s.getByTestId("ctl-leave").click();
  await expect(s.getByTestId("video-over")).toHaveAttribute("data-reason", "left");
  await expect(page.getByTestId("meeting-count")).toContainText("1", { timeout: 20_000 });

  // student comes back, then the teacher ends the lesson for everyone
  await s.getByTestId("video-rejoin").click();
  await expect(s.getByTestId("meeting")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByTestId("meeting-count")).toContainText("2", { timeout: 20_000 });
  await (await control(page, "ctl-end")).click();
  await expect(page.getByTestId("video-over")).toHaveAttribute("data-reason", "ended", { timeout: 20_000 });
  await expect(s.getByTestId("video-over")).toHaveAttribute("data-reason", "ended", { timeout: 20_000 });

  // an outsider cannot even see the room
  const octx = await browser.newContext();
  const o = await octx.newPage();
  await login(o, OUTSIDER);
  await o.goto(roomUrl);
  await expect(o.getByTestId("video-error")).toBeVisible({ timeout: 20_000 });
  await octx.close();
  await sctx.close();
});

test("a student cannot create a lesson and the tab shows no teacher form", async ({ page }) => {
  const teacher = await me(TEACHER);
  const gid = await groupId(teacher.token);
  await login(page, STUDENT);
  await page.goto(`/groups/${gid}?tab=video`);
  await expect(page.getByTestId("video-lessons")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByTestId("video-create-form")).toHaveCount(0);
  const studentToken = await apiToken(STUDENT, PASSWORD);
  const res = await fetch(`${API_URL}/api/v1/groups/${gid}/video-rooms`, {
    method: "POST", headers: { Authorization: `Bearer ${studentToken}`, "Content-Type": "application/json" },
    body: JSON.stringify({ title: "Hack", start_now: true }),
  });
  expect(res.status).toBe(403);
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1);
});
