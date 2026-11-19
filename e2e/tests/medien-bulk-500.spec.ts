import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { expect, test, type Page } from "@playwright/test";

import { ADMIN, API_URL, loginViaForm } from "./helpers";

// Admin → Medien → Musik: the bulk upload of up to 500 songs on the real local stack (backend + database + ffmpeg, FFMPEG_BIN):
// 500 different files in one go (counts, percent, each stored once, the metadata queue reads them all), an interrupted upload (page reload in the
// middle) that continues with only the missing files, duplicates (already on the server / twice in the list / same name other content), a lost
// connection on one file + "retry the failed ones", and an upload that keeps running while the admin opens another admin page. Local stack only.
const FFMPEG = process.env.FFMPEG_BIN ?? "ffmpeg";
const TAG = `B${Date.now().toString(36)}`;
const work = mkdtempSync(join(tmpdir(), "bulk-500-"));

// one short real MP3; every test file = it + a unique tail (decoders ignore trailing bytes, the SHA-256 differs)
const base = (() => {
  const p = join(work, "base.mp3");
  execFileSync(FFMPEG, ["-nostdin", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=500:duration=1", "-c:a", "libmp3lame", "-b:a", "32k", p], { stdio: "pipe" });
  return readFileSync(p);
})();
const file = (name: string, unique: string) => ({ name: `${name}.mp3`, mimeType: "audio/mpeg", buffer: Buffer.concat([base, Buffer.from(`\0${TAG}-${unique}`)]) });

async function token() {
  const res = await fetch(`${API_URL}/api/v1/auth/login`, { method: "POST", headers: { "Content-Type": "application/json", "X-Forwarded-For": `10.94.${Math.floor(Math.random() * 250)}.${Math.floor(Math.random() * 250)}` }, body: JSON.stringify({ identifier: ADMIN.email, password: ADMIN.password }) });
  expect(res.status).toBe(200);
  return (await res.json()).access_token as string;
}
async function songsLike(admin: string, q: string) {
  const res = await fetch(`${API_URL}/api/v1/admin/medien/songs?q=${encodeURIComponent(q)}&page_size=100`, { headers: { Authorization: `Bearer ${admin}` } });
  return (await res.json()) as { total: number; items: { id: string; title: string; duration_ms: number | null; metadata_status: string }[] };
}
async function adminLogin(page: Page) {
  await page.addInitScript(() => localStorage.setItem("vizu-language", JSON.stringify({ state: { language: "de" }, version: 0 })));
  await loginViaForm(page, ADMIN.email, ADMIN.password);
  await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
  await page.getByRole("button", { name: "Bestätigen" }).click();
  await expect(page).toHaveURL(/\/admin/);
}
const num = async (page: Page, id: string) => Number(await page.getByTestId(id).textContent());

test.describe.serial("Musik bulk upload: 500 songs", () => {
  test.skip(({ isMobile }) => isMobile, "an admin task on a computer");
  let admin = "";

  test.beforeAll(async () => { admin = await token(); });
  test.afterAll(async () => {
    test.setTimeout(600_000);
    // remove everything this spec made, 4 requests at a time (100 parallel deletes exhaust the backend's DB pool: see known-issues #23)
    for (let round = 0; round < 20; round += 1) {
      const { items } = await songsLike(admin, TAG);
      if (!items.length) break;
      for (let i = 0; i < items.length; i += 4) {
        await Promise.all(items.slice(i, i + 4).map((s) => fetch(`${API_URL}/api/v1/admin/medien/songs/${s.id}`, { method: "DELETE", headers: { Authorization: `Bearer ${admin}` } })));
      }
    }
    rmSync(work, { recursive: true, force: true });
  });

  test("500 different files in one go: every file stored once, the numbers and the percent, the metadata queue reads all of them", async ({ page }) => {
    test.setTimeout(600_000);
    await adminLogin(page);
    await page.goto("/admin/medien/musik");
    const files = Array.from({ length: 500 }, (_, i) => file(`${TAG}-full-${String(i + 1).padStart(3, "0")}`, `full-${i}`));
    await page.getByTestId("bulk-file").setInputFiles(files);
    await expect(page.getByTestId("bulk-total")).toHaveText("500");
    await expect(page.getByTestId("bulk-row")).toHaveCount(50); // one page of the list
    await expect(page.getByTestId("bulk-pager")).toContainText("Seite 1 / 10");
    await expect.poll(() => page.locator('[data-testid="bulk-row"][data-state="hashing"]').count(), { timeout: 60_000 }).toBe(0);
    const started = Date.now();
    await page.getByTestId("bulk-start").click();
    await expect.poll(() => num(page, "bulk-uploaded"), { timeout: 420_000, intervals: [2000] }).toBe(500);
    const uploadSeconds = Math.round((Date.now() - started) / 1000);
    await expect(page.getByTestId("bulk-failed")).toHaveText("0");
    await expect(page.getByTestId("bulk-remaining")).toHaveText("0");
    await expect(page.getByTestId("bulk-percent")).toHaveText("100%");
    await expect(page.getByTestId("bulk-summary")).toContainText("500 hochgeladen · 500 insgesamt");
    await expect.poll(() => num(page, "bulk-processing-count"), { timeout: 240_000, intervals: [3000] }).toBe(0);
    const doneSeconds = Math.round((Date.now() - started) / 1000);
    expect((await songsLike(admin, `${TAG}-full-`)).total).toBe(500);
    const sample = (await songsLike(admin, `${TAG}-full-025`)).items[0];
    expect(sample.metadata_status).toBe("OK");
    expect(sample.duration_ms).toBeGreaterThan(900);
    await page.getByTestId("bulk-page-next").click();
    await expect(page.getByTestId("bulk-row").first()).toHaveAttribute("data-state", "done");
    await expect(page.getByTestId("bulk-row").first().getByTestId("bulk-info")).toContainText("MP3 · 0:01");
    await page.screenshot({ path: "test-results/bulk-500-done.png", fullPage: false });
    console.log(`BULK 500: uploaded in ${uploadSeconds} s, metadata of all 500 read after ${doneSeconds} s`);
    await page.getByTestId("bulk-clear").click();
    await expect(page.getByTestId("bulk-row")).toHaveCount(0);
  });

  test("an interrupted upload (reload in the middle) continues with only the missing files — nothing twice", async ({ page }) => {
    test.setTimeout(300_000);
    await adminLogin(page);
    await page.goto("/admin/medien/musik");
    // real files on the disk: choosing them again gives the same name + size + date (like an admin picking the same folder again)
    const files = Array.from({ length: 120 }, (_, i) => {
      const f = file(`${TAG}-resume-${String(i + 1).padStart(3, "0")}`, `resume-${i}`);
      const path = join(work, f.name);
      writeFileSync(path, f.buffer);
      return path;
    });
    await page.getByTestId("bulk-file").setInputFiles(files);
    await expect.poll(() => page.locator('[data-testid="bulk-row"][data-state="hashing"]').count(), { timeout: 60_000 }).toBe(0);
    await page.getByTestId("bulk-start").click();
    await expect.poll(() => num(page, "bulk-uploaded"), { timeout: 120_000, intervals: [200] }).toBeGreaterThanOrEqual(30);
    await page.waitForTimeout(1500); // the list is saved in the browser (at most once a second)
    page.on("dialog", (d) => void d.accept()); // "leave the page?" while uploading
    await page.reload();
    const restored = page.getByTestId("bulk-restored");
    await expect(restored).toBeVisible({ timeout: 20_000 });
    const uploadedBefore = await num(page, "bulk-uploaded");
    expect(uploadedBefore).toBeGreaterThanOrEqual(30);
    expect(uploadedBefore).toBeLessThan(120);
    await expect(restored).toContainText(`${uploadedBefore} von 120`);
    const onServer = (await songsLike(admin, `${TAG}-resume-`)).total;
    expect(onServer).toBeGreaterThanOrEqual(uploadedBefore); // a file that was arriving during the reload may already be stored
    // the same 120 files again: only the missing ones are sent
    const sent: string[] = [];
    page.on("request", (r) => { if (r.method() === "POST" && /\/admin\/medien\/songs$/.test(r.url())) sent.push(r.url()); });
    await page.getByTestId("bulk-file").setInputFiles(files);
    await expect(page.getByTestId("bulk-note")).toContainText("wieder zugeordnet");
    await expect(page.getByTestId("bulk-total")).toHaveText("120");
    await page.getByTestId("bulk-start").click();
    await expect.poll(async () => (await num(page, "bulk-uploaded")) + (await num(page, "bulk-dups")), { timeout: 180_000, intervals: [1000] }).toBe(120);
    await expect(page.getByTestId("bulk-failed")).toHaveText("0");
    expect(sent.length).toBe(120 - uploadedBefore); // finished rows were never sent again
    expect((await songsLike(admin, `${TAG}-resume-`)).total).toBe(120); // every file exactly once on the server
    await expect(page.getByTestId("bulk-restored")).toHaveCount(0);
    await page.getByTestId("bulk-clear").click();
  });

  test("duplicates: already on the server, twice in the list, same name with other content; a lost connection + retry; other admin page meanwhile", async ({ page }) => {
    test.setTimeout(300_000);
    await adminLogin(page);
    await page.goto("/admin/medien/musik");
    const again = file(`${TAG}-full-001`, "full-0"); // uploaded in the first test
    const fresh = file(`${TAG}-dup-neu`, "dup-1");
    const twice = { ...fresh, name: `${TAG}-dup-neu-kopie.mp3` }; // the same bytes under another name
    const sameName = file(`${TAG}-full-002`, "other-content"); // the name of an uploaded file, other content
    const flaky = file(`${TAG}-dup-wackel`, "dup-2");
    let failOnce = true;
    await page.route("**/api/v1/admin/medien/songs", async (route) => {
      const body = route.request().postDataBuffer()?.toString("latin1") ?? "";
      if (failOnce && body.includes(`${TAG}-dup-wackel.mp3`)) { failOnce = false; await route.abort("connectionreset"); return; }
      await route.continue();
    });
    await page.getByTestId("bulk-file").setInputFiles([again, fresh, twice, sameName, flaky]);
    await expect.poll(() => page.locator('[data-testid="bulk-row"][data-state="hashing"]').count(), { timeout: 30_000 }).toBe(0);
    const row = (name: string) => page.locator(`[data-testid="bulk-row"][data-file="${name}"]`);
    await expect(row(again.name)).toHaveAttribute("data-state", "dup");
    await expect(row(again.name).getByTestId("bulk-dup")).toContainText("schon als");
    await expect(row(twice.name)).toHaveAttribute("data-state", "dup");
    await expect(row(twice.name).getByTestId("bulk-dup")).toContainText("in dieser Liste");
    await expect(row(sameName.name)).toHaveAttribute("data-state", "wait"); // same name, other content: NOT a duplicate
    await page.getByTestId("bulk-start").click();
    await expect(row(flaky.name)).toHaveAttribute("data-state", "error", { timeout: 60_000 });
    await expect(row(fresh.name)).toHaveAttribute("data-state", "done", { timeout: 60_000 });
    await expect(row(sameName.name)).toHaveAttribute("data-state", "done");
    await expect(page.getByTestId("bulk-summary")).toContainText("2 hochgeladen · 1 mit Fehler · 2 doppelt · 5 insgesamt");
    await page.getByTestId("bulk-retry-failed").click();
    await expect(row(flaky.name)).toHaveAttribute("data-state", "done", { timeout: 60_000 });
    // a deliberate copy of a song that is already there
    await row(again.name).getByTestId("bulk-allow-dup").click();
    await page.getByTestId("bulk-start").click();
    await expect(row(again.name)).toHaveAttribute("data-state", "done", { timeout: 60_000 });
    expect((await songsLike(admin, `${TAG}-full-001`)).total).toBe(2);
    expect((await songsLike(admin, `${TAG}-full-002`)).total).toBe(2); // the original + the other file with the same name
    expect((await songsLike(admin, `${TAG}-dup-neu`)).total).toBe(1); // the copy in the list was not sent
    await page.unroute("**/api/v1/admin/medien/songs");
    await page.getByTestId("bulk-clear").click();

    // the upload keeps running while the admin looks at another admin page
    const more = Array.from({ length: 60 }, (_, i) => file(`${TAG}-nav-${String(i + 1).padStart(2, "0")}`, `nav-${i}`));
    await page.getByTestId("bulk-file").setInputFiles(more);
    await expect.poll(() => page.locator('[data-testid="bulk-row"][data-state="hashing"]').count(), { timeout: 30_000 }).toBe(0);
    await page.getByTestId("bulk-start").click();
    await expect.poll(() => num(page, "bulk-uploaded"), { timeout: 60_000, intervals: [200] }).toBeGreaterThanOrEqual(5);
    await page.getByRole("link", { name: "Bibliothek" }).first().click(); // client-side navigation inside the admin panel
    await expect(page).toHaveURL(/\/admin\/medien\/bibliothek/);
    await page.waitForTimeout(3000);
    await page.getByRole("link", { name: "Musik" }).first().click();
    await expect(page).toHaveURL(/\/admin\/medien\/musik/);
    await expect.poll(() => num(page, "bulk-uploaded"), { timeout: 120_000, intervals: [1000] }).toBe(60);
    expect((await songsLike(admin, `${TAG}-nav-`)).total).toBe(60);
    await page.getByTestId("bulk-clear").click();
  });
});
