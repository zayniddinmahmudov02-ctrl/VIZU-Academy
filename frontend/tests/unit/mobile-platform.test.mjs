import assert from "node:assert/strict";
import { test } from "node:test";

import { detectPlatform, formatBytes, groupChecksum, isUpdateAvailable } from "../../src/features/mobile-app/utils/platform.ts";

const IPHONE_SAFARI = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1";
const IPHONE_CHROME = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/130.0 Mobile/15E148 Safari/604.1";
const IPAD_DESKTOP_MODE = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15";
const ANDROID_CHROME = "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Mobile Safari/537.36";
const TELEGRAM_IOS = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Telegram-iOS";
const WINDOWS = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36";

test("iPhone Safari / Chrome / Telegram", () => {
  assert.deepEqual(detectPlatform(IPHONE_SAFARI), { os: "ios", iosBrowser: "safari", inAppBrowser: false });
  assert.equal(detectPlatform(IPHONE_CHROME).iosBrowser, "chrome");
  assert.deepEqual(detectPlatform(TELEGRAM_IOS), { os: "ios", iosBrowser: "other", inAppBrowser: true });
});

test("iPad in desktop mode is iOS only with a touch screen", () => {
  assert.equal(detectPlatform(IPAD_DESKTOP_MODE, 5).os, "ios");
  assert.equal(detectPlatform(IPAD_DESKTOP_MODE, 0).os, "desktop");
});

test("Android and desktop", () => {
  assert.deepEqual(detectPlatform(ANDROID_CHROME), { os: "android", iosBrowser: null, inAppBrowser: false });
  assert.equal(detectPlatform(WINDOWS).os, "desktop");
  assert.equal(detectPlatform("").os, "desktop");
});

test("update check compares versionCodes", () => {
  assert.equal(isUpdateAvailable("1", 2), true);
  assert.equal(isUpdateAvailable("2", 2), false);
  assert.equal(isUpdateAvailable(3, 2), false);
  assert.equal(isUpdateAvailable(undefined, 2), false);
  assert.equal(isUpdateAvailable("abc", 2), false);
  assert.equal(isUpdateAvailable("1", null), false);
});

test("sizes and checksums", () => {
  assert.equal(formatBytes(4220980), "4.0 MB");
  assert.equal(formatBytes(2048), "2 KB");
  assert.equal(formatBytes(0), "0 B");
  assert.equal(groupChecksum("AB12CD34EF56AB12CD34"), "ab12cd34 ef56ab12 cd34");
});
