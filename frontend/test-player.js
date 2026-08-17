const { chromium } = require("playwright");

const SCREENSHOT_DIR = "C:\\Users\\user\\AppData\\Local\\Temp\\claude\\d--VIZU-Academy\\8259b631-caa9-4cbb-bf2f-c2e3fc430c9c\\scratchpad\\screenshots";
const fs = require("fs");
fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

const EMAIL = process.env.TEST_EMAIL;
const PASSWORD = process.env.TEST_PASSWORD;
const LESSON_ID = "dc302426-1372-4b29-8509-c2519a591d9b"; // A1 lesson 1, free, has a real video

let shotN = 0;
async function shot(page, label) {
  shotN += 1;
  const path = `${SCREENSHOT_DIR}\\${String(shotN).padStart(2, "0")}-${label}.png`;
  await page.screenshot({ path });
  console.log(`SCREENSHOT: ${path}`);
}

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await context.newPage();

  const consoleErrors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  page.on("pageerror", (err) => consoleErrors.push(`PAGEERROR: ${err.message}`));

  // Test-only workaround: production serves frontend+backend from the
  // same origin (nginx proxies /api/*), so the backend's relative
  // video_url resolves correctly there. This local test runs the
  // frontend on localhost:3000 against the real production backend
  // (a different origin), so the relative URL would resolve against
  // the wrong host. Rewrite it to absolute here, in the test harness
  // only — no product code is touched.
  await page.route("**/api/v1/videos/by-lesson/**", async (route) => {
    const response = await route.fetch();
    const json = await response.json();
    if (json.video_url && json.video_url.startsWith("/")) {
      json.video_url = "https://vizu-deutsch.com" + json.video_url;
    }
    await route.fulfill({ response, json });
  });

  console.log("--- Logging in ---");
  await page.goto("http://localhost:3000/login", { waitUntil: "networkidle" });
  await page.fill('input[type="email"]', EMAIL);
  await page.fill('input[type="password"]', PASSWORD);
  await page.click('button[type="submit"]');
  await page.waitForURL(/dashboard/, { timeout: 15000 });
  console.log("Logged in, on:", page.url());

  console.log("--- Navigating to lesson video section ---");
  await page.goto(`http://localhost:3000/lessons/${LESSON_ID}/video`, { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);
  await shot(page, "initial-load");

  // Wait for the video element to actually exist
  const videoExists = await page.locator("video").count();
  console.log("Video element count:", videoExists);

  if (videoExists === 0) {
    console.log("BODY TEXT SNIPPET:", (await page.locator("body").innerText()).slice(0, 500));
    console.log("CONSOLE ERRORS SO FAR:", JSON.stringify(consoleErrors, null, 2));
    await browser.close();
    process.exit(1);
  }

  // Wait for duration to be nonzero (metadata loaded)
  await page.waitForFunction(() => {
    const v = document.querySelector("video");
    return v && v.duration > 0;
  }, { timeout: 20000 });

  const initialDuration = await page.evaluate(() => document.querySelector("video").duration);
  console.log("Video duration (s):", initialDuration);

  // --- Play/Pause ---
  console.log("--- Testing Play ---");
  const playButton = page.getByRole("button", { name: /abspielen|play/i }).first();
  await playButton.click();
  await page.waitForTimeout(1500);
  const playingAfterClick = await page.evaluate(() => !document.querySelector("video").paused);
  console.log("Playing after click:", playingAfterClick);
  await shot(page, "after-play");

  console.log("--- Testing Pause ---");
  const pauseButton = page.getByRole("button", { name: /pausieren|pause/i }).first();
  await pauseButton.click();
  await page.waitForTimeout(500);
  const pausedAfterClick = await page.evaluate(() => document.querySelector("video").paused);
  console.log("Paused after click:", pausedAfterClick);

  // --- Seek to a known position first via direct set for deterministic skip testing ---
  await page.evaluate(() => { document.querySelector("video").currentTime = 100; });
  await page.waitForTimeout(300);
  let t = await page.evaluate(() => document.querySelector("video").currentTime);
  console.log("Time after setting to 100:", t);

  // --- Test 15s forward skip x5 ---
  console.log("--- Testing 15s forward skip x5 ---");
  const fwdButton = page.getByRole("button", { name: /15 Sekunden vor/i });
  for (let i = 0; i < 5; i++) {
    await fwdButton.click();
    await page.waitForTimeout(150);
  }
  t = await page.evaluate(() => document.querySelector("video").currentTime);
  console.log(`Time after 5x forward-15s clicks (expect ~175): ${t}`);
  await shot(page, "after-forward-skips");

  // --- Test 15s backward skip x5 ---
  console.log("--- Testing 15s backward skip x5 ---");
  const backButton = page.getByRole("button", { name: /15 Sekunden zurück/i });
  for (let i = 0; i < 5; i++) {
    await backButton.click();
    await page.waitForTimeout(150);
  }
  t = await page.evaluate(() => document.querySelector("video").currentTime);
  console.log(`Time after 5x backward-15s clicks (expect ~100): ${t}`);
  await shot(page, "after-backward-skips");

  // --- Test seek bar click-to-seek ---
  console.log("--- Testing seek bar click ---");
  const seekBar = page.locator('input[type="range"][aria-label="Videoposition"]');
  const seekBox = await seekBar.boundingBox();
  await page.mouse.click(seekBox.x + seekBox.width * 0.7, seekBox.y + seekBox.height / 2);
  await page.waitForTimeout(500);
  t = await page.evaluate(() => document.querySelector("video").currentTime);
  console.log(`Time after clicking seek bar at 70% (expect ~${(initialDuration * 0.7).toFixed(0)}): ${t}`);
  await shot(page, "after-seekbar-click");

  // --- Test seek bar drag ---
  console.log("--- Testing seek bar drag ---");
  await page.mouse.move(seekBox.x + seekBox.width * 0.7, seekBox.y + seekBox.height / 2);
  await page.mouse.down();
  await page.mouse.move(seekBox.x + seekBox.width * 0.2, seekBox.y + seekBox.height / 2, { steps: 10 });
  await page.waitForTimeout(200);
  const timeDuringDrag = await page.evaluate(() => document.querySelector("video").currentTime);
  console.log(`Time DURING drag (should NOT have committed the seek yet, expect still ~${(initialDuration * 0.7).toFixed(0)}): ${timeDuringDrag}`);
  await page.mouse.up();
  await page.waitForTimeout(500);
  t = await page.evaluate(() => document.querySelector("video").currentTime);
  console.log(`Time AFTER drag release (expect ~${(initialDuration * 0.2).toFixed(0)}): ${t}`);
  await shot(page, "after-seekbar-drag");

  // Check for snap-back: read time again after a moment
  await page.waitForTimeout(1000);
  const tAfterSettle = await page.evaluate(() => document.querySelector("video").currentTime);
  console.log(`Time 1s after drag release (checking no snap-back): ${tAfterSettle}`);

  // --- Volume / Mute ---
  console.log("--- Testing mute ---");
  const muteButton = page.getByRole("button", { name: /stummschalten|stummschaltung/i }).first();
  await muteButton.click();
  await page.waitForTimeout(300);
  const mutedState = await page.evaluate(() => document.querySelector("video").muted);
  console.log("Muted after click:", mutedState);
  await muteButton.click();
  await page.waitForTimeout(300);
  const unmutedState = await page.evaluate(() => document.querySelector("video").muted);
  console.log("Muted after second click (should be false):", unmutedState);

  // --- Settings / speed ---
  console.log("--- Testing settings/speed dropdown ---");
  const settingsButton = page.getByRole("button", { name: /einstellungen/i });
  await settingsButton.click();
  await page.waitForTimeout(300);
  await shot(page, "settings-open");
  const speedOption = page.getByRole("button", { name: "1.5x" });
  await speedOption.click();
  await page.waitForTimeout(300);
  const rate = await page.evaluate(() => document.querySelector("video").playbackRate);
  console.log("Playback rate after selecting 1.5x:", rate);

  // --- Fullscreen ---
  console.log("--- Testing fullscreen toggle ---");
  const fsButton = page.getByRole("button", { name: /vollbild/i });
  await fsButton.click();
  await page.waitForTimeout(500);
  const isFullscreen = await page.evaluate(() => !!document.fullscreenElement);
  console.log("Fullscreen active:", isFullscreen);
  await shot(page, "fullscreen-attempt");

  console.log("--- Final console errors ---");
  console.log(JSON.stringify(consoleErrors, null, 2));

  await browser.close();
})().catch((err) => {
  console.error("SCRIPT FAILED:", err);
  process.exit(1);
});
