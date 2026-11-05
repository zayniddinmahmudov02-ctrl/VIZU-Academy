import { expect, test, type Page } from "@playwright/test";

import { createStudent, loginViaForm, PASSWORD, useLanguage } from "./helpers";

// Battle audio (Web Audio synth, no files): settings panel persists on the device, and a full practice round with
// sound on runs without page errors (AudioContext is created by the first click). Local stack only.

async function student(page: Page) {
  await useLanguage(page, "de");
  await loginViaForm(page, await createStudent(), PASSWORD);
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 20_000 });
}

test("audio settings: mute, music/effects toggles and volume are saved on the device", async ({ page }) => {
  await student(page);
  await page.goto("/battle");
  await expect(page.getByTestId("battle-home")).toBeVisible({ timeout: 20_000 });
  const button = page.getByTestId("battle-audio-button").first();
  await button.click();
  const panel = page.getByTestId("battle-audio-panel");
  await expect(panel).toContainText("Sound-Einstellungen");
  await expect(page.getByTestId("battle-audio-music")).toHaveAttribute("aria-checked", "true");
  await page.getByTestId("battle-audio-music").click();
  await expect(page.getByTestId("battle-audio-music")).toHaveAttribute("aria-checked", "false");
  await expect(page.getByTestId("battle-audio-music-volume")).toBeDisabled();
  await page.getByTestId("battle-audio-sfx-volume").fill("30");
  await page.getByTestId("battle-audio-mute").click();
  await expect(page.getByTestId("battle-audio-mute")).toContainText("Ton an");

  await page.reload();
  await expect(page.getByTestId("battle-home")).toBeVisible({ timeout: 20_000 });
  await page.getByTestId("battle-audio-button").first().click();
  await expect(page.getByTestId("battle-audio-music")).toHaveAttribute("aria-checked", "false");
  await expect(page.getByTestId("battle-audio-sfx-volume")).toHaveValue("30");
  await expect(page.getByTestId("battle-audio-mute")).toContainText("Ton an");
  const stored = await page.evaluate(() => JSON.parse(localStorage.getItem("vizu-battle-audio") ?? "{}"));
  expect(stored).toMatchObject({ muted: true, music: false, sfx: true, sfxVolume: 0.3 });
});

test("practice match with sound on: no page errors, timer warning, sounds never break the round", async ({ page }) => {
  test.setTimeout(90_000);
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await student(page);
  await page.goto("/battle");
  await page.getByTestId("battle-practice").click(); // first gesture: creates the AudioContext, music starts
  await expect(page).toHaveURL(/\/battle\/match\//);
  const arena = page.getByTestId("battle-arena");
  await expect(arena).toBeVisible({ timeout: 15_000 });
  // let the clock run into the last 5 s: the ring pulses (the tick sound uses the same server deadline)
  await expect(page.locator(".bt-timer-warn").first()).toBeVisible({ timeout: 15_000 });
  await expect(arena).toHaveAttribute("data-phase", "reveal", { timeout: 15_000 });
  await expect(arena).toHaveAttribute("data-round", "2", { timeout: 15_000 });
  await page.getByTestId("answer-1").click();
  await expect(arena).toHaveAttribute("data-phase", "reveal", { timeout: 15_000 });
  expect(await page.evaluate(() => typeof (window.AudioContext ?? (window as unknown as { webkitAudioContext?: unknown }).webkitAudioContext))).toBe("function");
  expect(errors, errors.join("\n")).toEqual([]);
});
