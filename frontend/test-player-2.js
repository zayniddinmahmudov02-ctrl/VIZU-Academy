const { chromium } = require("playwright");
const fs = require("fs");

const SCREENSHOT_DIR = "C:\\Users\\user\\AppData\\Local\\Temp\\claude\\d--VIZU-Academy\\8259b631-caa9-4cbb-bf2f-c2e3fc430c9c\\scratchpad\\screenshots";
fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

const EMAIL = process.env.TEST_EMAIL;
const PASSWORD = process.env.TEST_PASSWORD;
const LESSON_ID = "dc302426-1372-4b29-8509-c2519a591d9b";

let shotN = 20;
async function shot(page, label) {
  shotN += 1;
  const path = `${SCREENSHOT_DIR}\\${String(shotN).padStart(2, "0")}-${label}.png`;
  await page.screenshot({ path });
  console.log(`SCREENSHOT: ${path}`);
}

(async () => {
  const browser = await chromium.launch();

  // ---- Round A: desktop, keyboard shortcuts + completion + progress persistence ----
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await context.newPage();
  const consoleErrors = [];
  page.on("console", (msg) => { if (msg.type() === "error") consoleErrors.push(msg.text()); });
  page.on("pageerror", (err) => consoleErrors.push(`PAGEERROR: ${err.message}`));

  await page.route("**/api/v1/videos/by-lesson/**", async (route) => {
    const response = await route.fetch();
    const json = await response.json();
    if (json.video_url && json.video_url.startsWith("/")) json.video_url = "https://vizu-deutsch.com" + json.video_url;
    await route.fulfill({ response, json });
  });

  await page.goto("http://localhost:3000/login", { waitUntil: "networkidle" });
  await page.fill('input[type="email"]', EMAIL);
  await page.fill('input[type="password"]', PASSWORD);
  await page.click('button[type="submit"]');
  await page.waitForURL(/dashboard/, { timeout: 15000 });

  await page.goto(`http://localhost:3000/lessons/${LESSON_ID}/video`, { waitUntil: "networkidle" });
  await page.waitForFunction(() => { const v = document.querySelector("video"); return v && v.duration > 0; }, { timeout: 20000 });

  console.log("--- Keyboard shortcuts ---");
  const videoBox = await page.locator("video").boundingBox();
  await page.mouse.click(videoBox.x + videoBox.width / 2, videoBox.y + videoBox.height / 2);
  await page.waitForTimeout(300);
  let playingState = await page.evaluate(() => !document.querySelector("video").paused);
  console.log("Playing after clicking video center (toggle 1):", playingState);

  await page.keyboard.press("Space");
  await page.waitForTimeout(300);
  playingState = await page.evaluate(() => !document.querySelector("video").paused);
  console.log("Playing after Space (should have toggled again):", playingState);

  await page.evaluate(() => { document.querySelector("video").currentTime = 300; });
  await page.waitForTimeout(200);
  await page.keyboard.press("ArrowRight");
  await page.waitForTimeout(300);
  let t = await page.evaluate(() => document.querySelector("video").currentTime);
  console.log(`Time after ArrowRight from 300 (expect ~305): ${t}`);

  await page.keyboard.press("ArrowLeft");
  await page.waitForTimeout(300);
  t = await page.evaluate(() => document.querySelector("video").currentTime);
  console.log(`Time after ArrowLeft (expect ~300): ${t}`);

  await page.keyboard.press("m");
  await page.waitForTimeout(200);
  let muted = await page.evaluate(() => document.querySelector("video").muted);
  console.log("Muted after pressing M:", muted);
  await page.keyboard.press("m");
  await page.waitForTimeout(200);

  console.log("--- Completion flow (seek to >=95%, wait for markComplete) ---");
  const duration = await page.evaluate(() => document.querySelector("video").duration);
  await page.evaluate((d) => { document.querySelector("video").currentTime = d * 0.97; }, duration);
  await page.waitForTimeout(500);
  // trigger a progress report + completion check the same way the real player does:
  // the player's periodic interval reports every 5s; force one seeked-report cycle
  await page.evaluate(() => {
    document.querySelector("video").dispatchEvent(new Event("seeked"));
  });
  await page.waitForTimeout(2000);
  await shot(page, "near-completion");
  const bodyText = await page.locator("body").innerText();
  console.log("Contains 'Video abgeschlossen':", bodyText.includes("Video abgeschlossen"));

  console.log("--- Reload page: verify progress persistence (resume) ---");
  await page.reload({ waitUntil: "networkidle" });
  await page.waitForTimeout(2000);
  const bodyText2 = await page.locator("body").innerText();
  console.log("After reload, contains 'Video abgeschlossen' (persisted server-side):", bodyText2.includes("Video abgeschlossen"));
  await shot(page, "after-reload-persistence");

  console.log("CONSOLE ERRORS (desktop round):", JSON.stringify(consoleErrors, null, 2));
  await context.close();

  // ---- Round B: mobile viewport ----
  const mobileContext = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  const mpage = await mobileContext.newPage();
  const mobileErrors = [];
  mpage.on("console", (msg) => { if (msg.type() === "error") mobileErrors.push(msg.text()); });
  mpage.on("pageerror", (err) => mobileErrors.push(`PAGEERROR: ${err.message}`));

  await mpage.route("**/api/v1/videos/by-lesson/**", async (route) => {
    const response = await route.fetch();
    const json = await response.json();
    if (json.video_url && json.video_url.startsWith("/")) json.video_url = "https://vizu-deutsch.com" + json.video_url;
    await route.fulfill({ response, json });
  });

  await mpage.goto("http://localhost:3000/login", { waitUntil: "networkidle" });
  await mpage.fill('input[type="email"]', EMAIL);
  await mpage.fill('input[type="password"]', PASSWORD);
  await mpage.click('button[type="submit"]');
  await mpage.waitForURL(/dashboard/, { timeout: 15000 });
  await mpage.goto(`http://localhost:3000/lessons/${LESSON_ID}/video`, { waitUntil: "networkidle" });
  await mpage.waitForFunction(() => { const v = document.querySelector("video"); return v && v.duration > 0; }, { timeout: 20000 });
  await mpage.waitForTimeout(1000);
  console.log("--- Mobile viewport screenshot ---");
  await shot(mpage, "mobile-viewport");

  // check no horizontal overflow of the control bar
  const overflow = await mpage.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  console.log("Horizontal overflow on mobile:", overflow);

  const fwdBtnBox = await mpage.getByRole("button", { name: /15 Sekunden vor/i }).boundingBox();
  console.log("Forward-15s button size (mobile):", fwdBtnBox);

  console.log("CONSOLE ERRORS (mobile round):", JSON.stringify(mobileErrors, null, 2));

  await browser.close();
})().catch((err) => {
  console.error("SCRIPT FAILED:", err);
  process.exit(1);
});
