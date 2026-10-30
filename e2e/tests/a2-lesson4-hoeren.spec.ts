import { expect, test, type Page } from "@playwright/test";

import { ADMIN, API_URL, loginViaForm, useLanguage } from "./helpers";

// A2 → 4. Unterricht → Hören: Text 1 / 2 / 3 against the throwaway stack. Seeds
// (D:\vz_tmp\work\gcr_e2e_seed.py + a2l4_e2e_seed.py, DB vizu_gcr_e2e) publish A2 lesson 4 with the
// OLD task "Hören: Familie Mannsberg"; `python -m app.scripts.a2_lesson4_hoeren apply` then removes it
// and creates the three Text tasks. gc-student2 gets an approved A2 test order (lesson 4 is paid). The audio files are tiny generated MP3 / M4A headers — test data.
const STUDENT = "gc-student1@example.com"; // no A2 access
const BUYER = "gc-student2@example.com"; // owns A2 (approved test order from the seed)
const PASSWORD = "Geheim123!";
const PAGE = "/admin/media-management/a2/lesson-4/hoeren";
const ADMIN_API = `${API_URL}/api/v1/admin/media-management/a2/lesson-4/hoeren`;

const mp3 = (seed: string) => Buffer.concat([Buffer.from("ID3\x04\x00\x00\x00\x00\x00\x00", "latin1"), Buffer.from(seed.repeat(200))]);
const m4a = (seed: string) => Buffer.concat([Buffer.from([0, 0, 0, 0x20]), Buffer.from("ftypM4A \x00\x00\x00\x00", "latin1"), Buffer.from(seed.repeat(200))]);

async function token(identifier: string, password: string) {
  const res = await fetch(`${API_URL}/api/v1/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ identifier, password }) });
  expect(res.status).toBe(200);
  return (await res.json()).access_token as string;
}

async function adminLogin(page: Page) {
  await useLanguage(page, "de");
  await loginViaForm(page, ADMIN.email, ADMIN.password);
  await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
  await page.getByRole("button", { name: "Bestätigen" }).click();
  await expect(page).toHaveURL(/\/admin/);
}

const slot = (page: Page, n: number) => page.locator(`[data-testid="a2l4-slot"][data-slot="${n}"]`);

async function upload(page: Page, n: number, name: string, mimeType: string, buffer: Buffer) {
  await slot(page, n).getByTestId("a2l4-file").setInputFiles({ name, mimeType, buffer });
}

async function noHorizontalScroll(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(1);
}

test.describe.serial("A2 4. Unterricht Hören — Text 1-3", () => {
  test("students and anonymous users can not use the management page", async () => {
    expect((await fetch(ADMIN_API)).status).toBe(401);
    const auth = { Authorization: `Bearer ${await token(STUDENT, PASSWORD)}` };
    expect((await fetch(ADMIN_API, { headers: auth })).status).toBe(403);
    expect((await fetch(`${ADMIN_API}/1/audio`, { headers: auth })).status).toBe(403);
    expect((await fetch(`${ADMIN_API}/1/active`, { method: "POST", headers: { ...auth, "Content-Type": "application/json" }, body: '{"active":true}' })).status).toBe(403);
  });

  test("admin: three independent uploads, validation, duplicate, verify, activate, replace", async ({ page, isMobile }) => {
    test.skip(isMobile, "uploads run once on desktop; the mobile run checks the layout below");
    await adminLogin(page);
    await page.goto("/admin/media-management");
    await page.getByTestId("mm-level").selectOption("A2");
    await page.getByTestId("mm-a2-lesson4-hoeren-link").click();
    await expect(page).toHaveURL(new RegExp(`${PAGE}$`));
    await expect(page.getByTestId("a2l4-slot")).toHaveCount(3);
    await expect(page.getByTestId("a2l4-hoeren")).not.toContainText("Mannsberg");
    for (const n of [1, 2, 3]) await expect(slot(page, n)).toHaveAttribute("data-state", "none");

    const seed = String(Date.now());
    await upload(page, 1, "A2 4.Unterricht Text 1.mp3", "audio/mpeg", mp3(`a${seed}`));
    await expect(slot(page, 1).getByTestId("a2l4-upload-state")).toHaveText("Hochgeladen", { timeout: 20_000 });
    await upload(page, 2, "A2 4.Unterricht Text 2.m4a", "audio/mp4", m4a(`b${seed}`));
    await expect(slot(page, 2).getByTestId("a2l4-upload-state")).toHaveText("Hochgeladen", { timeout: 20_000 });
    await upload(page, 3, "A2 4.Unterricht Text 3.mp3", "audio/mpeg", mp3(`c${seed}`));
    await expect(slot(page, 3).getByTestId("a2l4-upload-state")).toHaveText("Hochgeladen", { timeout: 20_000 });
    await expect(slot(page, 1).getByTestId("a2l4-file-name")).toHaveText("A2 4.Unterricht Text 1.mp3");
    await expect(slot(page, 2).getByTestId("a2l4-size")).toContainText("M4A");
    await expect(slot(page, 3).getByTestId("a2l4-verification")).toContainText("noch nicht angehört");

    // wrong formats: refused, the slot keeps its audio
    await upload(page, 3, "Text 3.wav", "audio/wav", Buffer.from("RIFF0000WAVEfmt "));
    await expect(slot(page, 3).getByTestId("a2l4-msg")).toContainText("Nur MP3 oder M4A");
    await expect(slot(page, 3)).toHaveAttribute("data-state", "error");
    await upload(page, 3, "Text 3.mp3", "audio/mpeg", m4a(`x${seed}`)); // M4A content named .mp3
    await expect(slot(page, 3).getByTestId("a2l4-msg")).toContainText("EXTENSION_MISMATCH", { timeout: 15_000 });
    await expect(slot(page, 3).getByTestId("a2l4-file-name")).toHaveText("A2 4.Unterricht Text 3.mp3");

    // the same content as Text 2 -> duplicate
    await upload(page, 3, "kopie.m4a", "audio/mp4", m4a(`b${seed}`));
    await expect(slot(page, 3).getByTestId("a2l4-msg")).toContainText("Doppelte Datei", { timeout: 15_000 });
    await expect(slot(page, 3).getByTestId("a2l4-msg")).toContainText("Hören: Text 2");

    // Text 1: listen, verify, activate
    await expect(slot(page, 1).getByTestId("a2l4-activate")).toBeDisabled();
    await slot(page, 1).getByTestId("a2l4-play").click();
    await expect(slot(page, 1).getByTestId("a2l4-player")).toBeVisible();
    await slot(page, 1).getByTestId("a2l4-verify").click();
    await expect(slot(page, 1).getByTestId("a2l4-verification")).toContainText("geprüft");
    await slot(page, 1).getByTestId("a2l4-activate").click();
    await expect(slot(page, 1)).toHaveAttribute("data-active", "true");

    // replacing Text 3 leaves Text 1 and Text 2 as they are
    await upload(page, 3, "Text 3 neu.mp3", "audio/mpeg", mp3(`d${seed}`));
    await expect(slot(page, 3).getByTestId("a2l4-file-name")).toHaveText("Text 3 neu.mp3", { timeout: 20_000 });
    await expect(slot(page, 1).getByTestId("a2l4-file-name")).toHaveText("A2 4.Unterricht Text 1.mp3");
    await expect(slot(page, 1)).toHaveAttribute("data-active", "true");
    await expect(slot(page, 2).getByTestId("a2l4-file-name")).toHaveText("A2 4.Unterricht Text 2.m4a");

    // delete Text 2's audio
    await slot(page, 2).getByTestId("a2l4-delete").click();
    await page.getByTestId("confirm-dialog-confirm").click();
    await expect(slot(page, 2)).toHaveAttribute("data-state", "none", { timeout: 15_000 });
    await expect(slot(page, 1)).toHaveAttribute("data-active", "true");
  });

  test("lesson page: only the active Text with a player; Familie Mannsberg is gone; paid audio stays closed", async ({ page }) => {
    const admin = await token(ADMIN.email, ADMIN.password);
    const overview = await (await fetch(ADMIN_API, { headers: { Authorization: `Bearer ${admin}` } })).json();
    const lessonId = overview.lesson_id as string;
    const text1 = overview.slots.find((s: { slot: number }) => s.slot === 1);
    expect(text1.is_published).toBe(true);
    const audio = `${API_URL}/api/v1/lesson-skills/${lessonId}/hoeren/${text1.listening_id}/audio`;
    expect((await fetch(audio)).status).toBe(401);
    expect((await fetch(audio, { headers: { Authorization: `Bearer ${await token(STUDENT, PASSWORD)}` } })).status).toBe(403); // lesson 4 is paid
    const ok = await fetch(audio, { headers: { Authorization: `Bearer ${admin}` } });
    expect(ok.status).toBe(200);
    expect(ok.headers.get("cache-control")).toBe("private, no-store");

    // a student who owns A2 (seed: approved test order) opens lesson 4
    const buyerAudio = await fetch(audio, { headers: { Authorization: `Bearer ${await token(BUYER, PASSWORD)}` } });
    expect(buyerAudio.status).toBe(200);
    await useLanguage(page, "de");
    await loginViaForm(page, BUYER, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);
    await page.goto(`/lektion/${lessonId}/hoeren`);
    const tasks = page.getByTestId("hoeren-task");
    await expect(tasks).toHaveCount(1, { timeout: 20_000 });
    await expect(tasks.first()).toContainText("Hören: Text 1");
    await expect(tasks.first().locator("audio")).toHaveCount(1, { timeout: 15_000 });
    await expect(page.locator("body")).not.toContainText("Mannsberg");
    await noHorizontalScroll(page);
  });

  test("admin page layout on this viewport", async ({ page }) => {
    await adminLogin(page);
    await page.goto(PAGE);
    await expect(page.getByTestId("a2l4-slot")).toHaveCount(3);
    await expect(slot(page, 1)).toHaveAttribute("data-active", "true");
    await noHorizontalScroll(page);
  });
});
