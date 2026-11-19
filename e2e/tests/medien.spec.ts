import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { expect, test, type Locator, type Page } from "@playwright/test";

import { ADMIN, API_URL, PASSWORD, createStudent, loginViaForm } from "./helpers";

// VIZU MEDIENWELT against the local stack (needs ffmpeg: FFMPEG_BIN for the backend and for this spec). Real files: a 4-page
// PDF, PNG covers, MP3s and an MP4 made by ffmpeg, SRT / VTT subtitles. Admin flows run in the German admin UI, student
// flows in Uzbek. Everything created here is removed again at the end through the admin API.
const FFMPEG = process.env.FFMPEG_BIN ?? "ffmpeg";
const TAG = `E2E${Date.now().toString(36)}`;
const work = mkdtempSync(join(tmpdir(), "medien-"));
const PNG = Buffer.from("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082", "hex");

function pdf(pages: number): Buffer {
  const objs: string[] = ["<</Type/Catalog/Pages 2 0 R>>", `<</Type/Pages/Kids[${Array.from({ length: pages }, (_, i) => `${3 + i * 2} 0 R`).join(" ")}]/Count ${pages}>>`];
  for (let i = 0; i < pages; i += 1) {
    const stream = `BT /F1 40 Tf 60 400 Td (Seite ${i + 1}) Tj ET`;
    objs.push(`<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 500]/Contents ${4 + i * 2} 0 R/Resources<</Font<</F1 ${3 + pages * 2} 0 R>>>>>>`, `<</Length ${stream.length}>>\nstream\n${stream}\nendstream`);
  }
  objs.push("<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>");
  let out = "%PDF-1.4\n";
  const offsets: number[] = [];
  objs.forEach((o, i) => { offsets.push(out.length); out += `${i + 1} 0 obj\n${o}\nendobj\n`; });
  const xref = out.length;
  out += `xref\n0 ${objs.length + 1}\n0000000000 65535 f \n${offsets.map((o) => `${String(o).padStart(10, "0")} 00000 n \n`).join("")}trailer\n<</Size ${objs.length + 1}/Root 1 0 R>>\nstartxref\n${xref}\n%%EOF\n`;
  return Buffer.from(out, "latin1");
}

function ffmpeg(args: string[]) { execFileSync(FFMPEG, ["-nostdin", "-v", "error", "-y", ...args], { stdio: "pipe" }); }
// every file has its own bytes (a comment tag with its name): the bulk upload refuses the same file twice since 2026-11-19
const mp3 = (name: string, seconds = 12, dir = work) => { const p = join(dir, name); ffmpeg(["-f", "lavfi", "-i", `sine=frequency=${300 + (name.length % 7) * 40}:duration=${seconds}`, "-c:a", "libmp3lame", "-metadata", `comment=${name}`, p]); return p; };
const mp4Path = () => { const p = join(work, "film.mp4"); ffmpeg(["-f", "lavfi", "-i", "testsrc=duration=20:size=320x180:rate=15", "-f", "lavfi", "-i", "sine=frequency=440:duration=20", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", p]); return p; };

const SRT = "1\n00:00:00,500 --> 00:00:03,000\nGuten Tag Welt\n\n2\n00:00:03,500 --> 00:00:05,500\nAuf Wiedersehen\n";
const VTT_UZ = "WEBVTT\n\n00:00:00.500 --> 00:00:03.000\nSalom dunyo\n";

async function token(email: string, password: string) {
  const res = await fetch(`${API_URL}/api/v1/auth/login`, { method: "POST", headers: { "Content-Type": "application/json", "X-Forwarded-For": `10.99.${Math.floor(Math.random() * 250)}.${Math.floor(Math.random() * 250)}` }, body: JSON.stringify({ identifier: email, password }) });
  expect(res.status, await res.clone().text()).toBe(200);
  return (await res.json()).access_token as string;
}
const call = async (method: string, url: string, bearer: string, body?: unknown) => {
  const res = await fetch(`${API_URL}/api/v1${url}`, { method, headers: { Authorization: `Bearer ${bearer}`, ...(body ? { "Content-Type": "application/json" } : {}) }, body: body ? JSON.stringify(body) : undefined });
  const text = await res.text();
  return { status: res.status, json: text && res.headers.get("content-type")?.includes("json") ? JSON.parse(text) : null };
};

async function adminLogin(page: Page) {
  await page.addInitScript(() => localStorage.setItem("vizu-language", JSON.stringify({ state: { language: "de" }, version: 0 })));
  await loginViaForm(page, ADMIN.email, ADMIN.password);
  await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
  await page.getByRole("button", { name: "Bestätigen" }).click();
  await expect(page).toHaveURL(/\/admin/);
}
async function studentLogin(page: Page, email: string, lang: "uz" | "de" = "uz") {
  await loginViaForm(page, email, PASSWORD);
  await expect(page).toHaveURL(/\/dashboard/);
  await page.evaluate((l) => localStorage.setItem("vizu-language", JSON.stringify({ state: { language: l }, version: 0 })), lang);
  await page.reload();
}
async function noHorizontalScroll(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
}
const search = async (page: Page, testId: string, text: string, cards: string, count: number) => {
  await expect(async () => { await page.getByTestId(testId).fill(text); await expect(page.getByTestId(cards)).toHaveCount(count, { timeout: 3000 }); }).toPass({ timeout: 20_000 });
};
const fillField = async (dialog: Locator, testId: string, value: string) => { await dialog.getByTestId(testId).fill(value); };

// the music player is started by a click, but headless Chromium is also told it may autoplay (restoring after a reload)
test.use({ launchOptions: { args: ["--autoplay-policy=no-user-gesture-required"] } });

test.describe.serial("Medienwelt", () => {
  test.skip(({ isMobile }) => isMobile, "content is created once (desktop); the phone layouts run in the last test");
  let student = "";
  let adminToken = "";
  const created = { books: [] as string[], songs: [] as string[], films: [] as string[], cats: [] as string[], playlists: [] as string[] };

  test.beforeAll(async () => {
    student = await createStudent();
    adminToken = await token(ADMIN.email, ADMIN.password);
  });

  test.afterAll(async () => {
    for (const id of created.playlists) await call("DELETE", `/admin/medien/playlists/${id}`, adminToken);
    for (const id of created.books) await call("DELETE", `/admin/medien/books/${id}`, adminToken);
    for (const id of created.songs) await call("DELETE", `/admin/medien/songs/${id}`, adminToken);
    for (const id of created.films) await call("DELETE", `/admin/medien/films/${id}`, adminToken);
    for (const id of created.cats) await call("DELETE", `/admin/medien/categories/${id}`, adminToken);
    rmSync(work, { recursive: true, force: true });
  });

  test("security: nothing of Medienwelt is open to anonymous users or students", async () => {
    const studentToken = await token(student, PASSWORD);
    for (const [method, url] of [["GET", "/medien/books"], ["GET", "/medien/songs"], ["GET", "/medien/films"], ["GET", "/admin/medien/stats"]] as const) {
      expect((await fetch(`${API_URL}/api/v1${url}`, { method })).status, url).toBe(401);
    }
    for (const [method, url] of [["GET", "/admin/medien/stats"], ["GET", "/admin/medien/books"], ["POST", "/admin/medien/books"], ["GET", "/admin/medien/purchases"], ["DELETE", "/admin/medien/songs/00000000-0000-0000-0000-000000000000"]] as const) {
      expect((await call(method, url, studentToken, method === "POST" ? { title: "x" } : undefined)).status, url).toBe(403);
    }
    expect((await fetch(`${API_URL}/api/v1/medien/stream/BOOK/00000000-0000-0000-0000-000000000000?token=x`)).status).toBe(401);
    expect((await fetch(`${API_URL}/protected_storage/medien/books/x.pdf`)).status).toBe(404);
  });

  test("admin: categories, free + paid books with cover and PDF", async ({ page }) => {
    await adminLogin(page);
    await page.goto("/admin/medien/bibliothek");
    await expect(page.getByTestId("books-admin")).toBeVisible();
    // the starting categories exist; a new one can be created, renamed, hidden
    for (const name of ["Literatur", "Grammatik", "Zertifikatsbücher", "Wortschatz", "Lektüren", "Prüfungsvorbereitung", "Sonstige Bücher"]) await expect(page.getByTestId("category-chip").filter({ hasText: name }).first()).toBeVisible();
    await page.getByTestId("category-new-input").fill(`${TAG} Krimi`);
    await page.getByTestId("category-add").click();
    const chip = page.locator(`[data-testid="category-chip"][data-name="${TAG} Krimi"]`);
    await expect(chip).toBeVisible();
    await expect(page.getByTestId("category-add")).toBeDisabled(); // empty input: nothing can be added
    await chip.getByTestId("category-rename").click();
    await page.getByTestId("category-edit-input").fill(`${TAG} Krimis`);
    await page.getByTestId("category-edit-save").click();
    await expect(page.locator(`[data-testid="category-chip"][data-name="${TAG} Krimis"]`)).toBeVisible();

    const make = async (title: string, opts: { paid?: boolean; offer?: boolean; level?: string; author: string }) => {
      await page.getByTestId("book-new").click();
      const d = page.getByTestId("book-dialog");
      await fillField(d, "f-title", title);
      await d.getByTestId("f-description").fill(`Beschreibung von ${title}`);
      await d.getByTestId("f-level").selectOption(opts.level ?? "A2");
      await fillField(d, "f-author", opts.author);
      await d.getByTestId("f-category").selectOption({ label: `${TAG} Krimis` });
      await fillField(d, "f-year", "2020");
      await d.getByTestId("f-status").selectOption("PUBLISHED");
      if (opts.paid) {
        await d.getByTestId("f-access").selectOption("PAID");
        await fillField(d, "f-price", "50000");
        await fillField(d, "f-old-price", "80000");
        if (opts.offer) await d.getByRole("checkbox", { name: "Sonderangebot" }).click();
      }
      await d.getByTestId("book-cover-file").setInputFiles({ name: "cover.png", mimeType: "image/png", buffer: PNG });
      await d.getByTestId("book-pdf-file").setInputFiles({ name: "buch.pdf", mimeType: "application/pdf", buffer: pdf(4) });
      await page.getByTestId("book-save").click();
      await expect(page.getByTestId("book-note")).toHaveText("Gespeichert.", { timeout: 30_000 });
      await page.getByTestId("book-close").click();
      await expect(page.getByTestId("book-dialog")).toHaveCount(0);
    };
    await make(`${TAG} Gratis`, { author: "Anna Autor", level: "A1" });
    await make(`${TAG} Premium`, { author: "Bernd Autor", paid: true, offer: true, level: "B1" });
    await page.getByTestId("books-search").fill(TAG);
    const rows = page.getByTestId("book-row");
    await expect(rows).toHaveCount(2);
    await expect(rows.filter({ hasText: "Premium" })).toContainText("50.000 UZS");
    await expect(rows.filter({ hasText: "Gratis" })).toContainText("Kostenlos");
    await expect(rows.first().getByTestId("status-pill")).toHaveText("Veröffentlicht");
    // an invalid PDF is refused with a readable message
    await page.getByTestId("book-new").click();
    const d = page.getByTestId("book-dialog");
    await fillField(d, "f-title", `${TAG} Defekt`);
    await d.getByTestId("book-pdf-file").setInputFiles({ name: "kaputt.pdf", mimeType: "application/pdf", buffer: Buffer.from("das ist kein pdf") });
    await page.getByTestId("book-save").click();
    await expect(page.getByTestId("book-note")).toContainText("nicht unterstützt", { timeout: 20_000 });
    await page.getByTestId("book-close").click();
    const list = (await call("GET", `/admin/medien/books?q=${TAG}`, adminToken)).json.items as { id: string; title: string }[];
    created.books.push(...list.map((b) => b.id));
    created.cats.push(...((await call("GET", "/admin/medien/categories?kind=BOOK", adminToken)).json as { id: string; name: string }[]).filter((c) => c.name.startsWith(TAG)).map((c) => c.id));
    expect(list.length).toBe(3); // the defective one was saved as a draft without file
  });

  test("student: Bibliothek shelves, filters, free book in the PDF reader (page resume), paid book locked", async ({ page }) => {
    await studentLogin(page, student);
    await page.goto("/medien");
    await expect(page.getByTestId("medien-title")).toHaveText("VIZU MEDIENWELT");
    for (const id of ["library", "music", "films"]) await expect(page.getByTestId(`medien-card-${id}`)).toBeVisible();
    await expect(page.getByRole("link", { name: "Medien" }).first()).toBeVisible();
    await page.getByTestId("medien-card-library").click();
    await expect(page).toHaveURL(/\/medien\/bibliothek/);
    await page.waitForTimeout(1200); // the shared page transition remounts a page once after a client-side navigation: let it settle
    await expect(page.getByTestId("bookshelves")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByTestId("shelf").first()).toBeVisible();

    // special offers at the top show the paid book with old and new price
    const offer = page.getByTestId("offer-card").filter({ hasText: `${TAG} Premium` });
    await expect(offer).toBeVisible();
    await expect(offer).toContainText("50.000");
    await expect(offer).toContainText("80.000");
    await expect(offer.getByTestId("book-buy")).toBeVisible();

    // category / search / level filters
    await search(page, "book-search", TAG, "book-card", 2);
    await page.getByTestId("book-level").selectOption("A1");
    await expect(page.getByTestId("book-card")).toHaveCount(1);
    await page.getByTestId("book-level").selectOption("");
    await search(page, "book-search", "Bernd", "book-card", 1); // by author
    await page.getByTestId("book-search").fill(TAG);
    await page.locator(`[data-testid="book-category"]`, { hasText: `${TAG} Krimis` }).click();
    await expect(page.getByTestId("book-card")).toHaveCount(2);
    await page.getByTestId("book-access").selectOption("FREE");
    await expect(page.getByTestId("book-card")).toHaveCount(1);
    await expect(page.getByTestId("book-card").first()).toHaveAttribute("data-free", "1");
    await page.screenshot({ path: "test-results/medien-bibliothek.png", fullPage: true });

    // free book: details -> reader -> next page, zoom -> close -> reopen on the saved page
    await page.getByTestId("book-card").first().click();
    await page.waitForTimeout(1200); // let the shared page transition finish (it remounts the page once)
    await expect(page.getByTestId("book-title")).toHaveText(`${TAG} Gratis`);
    await expect(page.getByTestId("book-author")).toHaveText("Anna Autor");
    await page.getByTestId("book-read").click();
    const reader = page.getByTestId("pdf-reader");
    await expect(reader.getByTestId("reader-canvas")).toBeVisible({ timeout: 30_000 });
    await expect(reader.getByTestId("reader-total")).toHaveText("/ 4");
    await expect(reader.getByTestId("reader-page")).toHaveValue("1");
    await reader.getByTestId("reader-next").click();
    await reader.getByTestId("reader-next").click();
    await expect(reader.getByTestId("reader-page")).toHaveValue("3");
    await reader.getByTestId("reader-zoom-in").click();
    await expect(reader.getByTestId("reader-zoom")).not.toHaveText("100%");
    await reader.getByTestId("reader-zoom-out").click();
    await expect(reader.getByTestId("reader-fullscreen")).toBeVisible();
    await page.waitForTimeout(1500); // the last page is saved (debounced)
    await reader.getByTestId("reader-close").click();
    await page.reload();
    await expect(page.getByTestId("book-read")).toContainText("3");
    await page.getByTestId("book-read").click();
    await expect(page.getByTestId("reader-page")).toHaveValue("3", { timeout: 30_000 });
    await page.keyboard.press("ArrowLeft");
    await expect(page.getByTestId("reader-page")).toHaveValue("2");
    await page.getByTestId("reader-close").click();

    // paid book: cover, text, price — no reader, buy button; the API refuses the file
    await page.goto("/medien/bibliothek");
    await page.getByTestId("book-search").fill(`${TAG} Premium`);
    await page.getByTestId("book-card").first().click();
    await page.waitForTimeout(1200); // let the shared page transition finish (it remounts the page once)
    await expect(page.getByTestId("book-locked-note")).toBeVisible();
    await expect(page.getByTestId("book-read")).toHaveCount(0);
    await expect(page.getByTestId("tag-price")).toContainText("50.000");
    const studentToken = await token(student, PASSWORD);
    const paidId = created.books.find((id) => id) as string;
    const paid = ((await call("GET", `/medien/books?q=${TAG}%20Premium`, studentToken)).json.items as { id: string; locked: boolean }[])[0];
    expect(paid.locked).toBe(true);
    // a paid book gives away its first pages only (all but the last of this 4-page book), never the original and never a download
    const preview = await call("POST", `/medien/books/${paid.id}/open`, studentToken);
    expect([preview.status, preview.json.mode, preview.json.preview_pages, preview.json.total_pages]).toEqual([200, "preview", 3, 4]);
    expect((await call("POST", `/medien/books/${paid.id}/download-link`, studentToken)).status).toBe(403);
    void paidId;
  });

  test("payment request (no receipt) -> Super Admin approves -> the paid book opens in full; revoke closes it again", async ({ page, browser }) => {
    await studentLogin(page, student);
    const studentToken = await token(student, PASSWORD);
    const paid = ((await call("GET", `/medien/books?q=${TAG}%20Premium`, studentToken)).json.items as { id: string }[])[0];
    await page.goto(`/medien/bibliothek/${paid.id}`);
    await page.getByTestId("book-buy").click();
    const modal = page.getByTestId("book-payment-modal");
    await expect(modal.getByTestId("pay-book-price")).toContainText("50.000");
    await modal.getByTestId("pay-variant-time").click(); // no receipt: the date and the time of the transfer
    await modal.getByTestId("pay-date").fill(new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Tashkent" }).format(new Date(Date.now() - 36 * 3600_000)));
    await modal.getByTestId("pay-time").fill("12:30");
    await modal.getByTestId("pay-submit").click();
    await expect(modal.getByTestId("pay-pending")).toBeVisible();
    await modal.getByTestId("pay-done").click();
    // a request gives no access: still only the preview, no download
    expect((await call("POST", `/medien/books/${paid.id}/open`, studentToken)).json.mode).toBe("preview");
    expect((await call("POST", `/medien/books/${paid.id}/download-link`, studentToken)).status).toBe(403);

    const ctx = await browser.newContext();
    const admin = await ctx.newPage();
    await adminLogin(admin);
    await admin.goto("/admin/medien/bibliothek");
    await admin.getByTestId("books-tab-payments").click();
    const request = admin.getByTestId("payment-row").filter({ hasText: student });
    await expect(request).toContainText(`${TAG} Premium`);
    await request.getByTestId("payment-review").click();
    await expect(admin.getByTestId("receipt-none")).toContainText("12:30");
    await expect(admin.getByTestId("payment-approve")).toBeDisabled(); // checked first, then approved
    await admin.getByTestId("payment-verified").click();
    await admin.getByTestId("payment-approve").click();
    await expect(admin.getByTestId("payment-message")).toContainText("freigeschaltet");
    await page.reload();
    await expect(page.getByTestId("book-read")).toBeVisible();
    await expect(page.getByTestId("book-download")).toBeVisible();
    expect((await call("POST", `/medien/books/${paid.id}/open`, studentToken)).json.mode).toBe("full");
    // the approval is a normal purchase: the old purchase list shows it and can revoke it
    await admin.goto("/admin/medien");
    await admin.getByTestId("purchases-filter").selectOption("GRANTED");
    await admin.getByTestId("purchase-row").filter({ hasText: student }).getByTestId("purchase-revoke").click();
    await expect(admin.getByTestId("purchases-message")).toBeVisible();
    expect((await call("POST", `/medien/books/${paid.id}/open`, studentToken)).json.mode).toBe("preview");
    // the dashboard numbers are the database numbers
    await admin.goto("/admin/medien");
    const stats = (await call("GET", "/admin/medien/stats", adminToken)).json;
    await expect(admin.getByTestId("stat-books").locator("p").first()).toHaveText(String(stats.books.total));
    await expect(admin.getByTestId("stat-books-free").locator("p").first()).toHaveText(String(stats.books.free));
    await expect(admin.getByTestId("stat-books-paid").locator("p").first()).toHaveText(String(stats.books.paid));
    await expect(admin.getByTestId("stat-songs").locator("p").first()).toHaveText(String(stats.songs.total));
    await ctx.close();
  });

  test("admin: bulk upload of 10 songs (one is not audio) + the same file again, per-file progress, edit, hide", async ({ page }) => {
    await adminLogin(page);
    await page.goto("/admin/medien/musik");
    const files = Array.from({ length: 9 }, (_, i) => ({ name: `${TAG}-song${i + 1}.mp3`, mimeType: "audio/mpeg", buffer: readFileSync(mp3(`${TAG}-song${i + 1}.mp3`)) }));
    files.splice(4, 0, { name: `${TAG}-kaputt.mp3`, mimeType: "audio/mpeg", buffer: Buffer.from("das ist keine audiodatei") });
    await page.getByTestId("bulk-defaults").getByLabel("Interpret (Vorgabe)").fill("VIZU Band");
    await page.getByTestId("bulk-defaults").getByLabel("Genre (Vorgabe)").fill("Pop");
    await page.getByTestId("bulk-file").setInputFiles(files);
    await expect(page.getByTestId("bulk-row")).toHaveCount(10);
    // an eleventh file is taken (the limit is 500 since 2026-11-19) — it is the same file as the first one, so it is marked as a duplicate and not sent
    await page.getByTestId("bulk-file").setInputFiles([{ name: "elf.mp3", mimeType: "audio/mpeg", buffer: files[0].buffer }]);
    await expect(page.getByTestId("bulk-row")).toHaveCount(11);
    await expect(page.locator('[data-testid="bulk-row"][data-file="elf.mp3"]')).toHaveAttribute("data-state", "dup");
    await page.getByTestId("bulk-row").nth(0).getByLabel("Album").fill("Testalbum");
    await page.getByTestId("bulk-row").nth(1).getByLabel("Niveau").selectOption("B1");
    await page.getByTestId("bulk-start").click();
    await expect(page.getByTestId("bulk-summary")).toContainText("9 hochgeladen", { timeout: 120_000 });
    await expect(page.getByTestId("bulk-summary")).toContainText("1 mit Fehler");
    await expect(page.getByTestId("bulk-summary")).toContainText("1 doppelt");
    await expect(page.locator('[data-testid="bulk-row"][data-state="error"]')).toHaveCount(1);
    await expect(page.locator('[data-testid="bulk-row"][data-state="error"]').getByTestId("bulk-error")).toContainText("nicht");
    await expect(page.locator('[data-testid="bulk-row"][data-state="done"]')).toHaveCount(9); // the failure did not stop the others

    await page.getByTestId("songs-search").fill(TAG);
    await expect(page.getByTestId("song-admin-row")).toHaveCount(9);
    const first = page.locator(`[data-testid="song-admin-row"][data-title="${TAG}-song1"]`);
    await expect(first).toContainText("VIZU Band");
    await expect(first).toContainText("Testalbum");
    await expect(first).toContainText("0:12");
    await first.getByTestId("song-edit").click();
    const d = page.getByTestId("song-dialog");
    await d.getByTestId("f-title").fill(`${TAG}-song1 neu`);
    await d.getByTestId("f-featured").check();
    await page.getByTestId("song-save").click();
    await expect(page.getByTestId("song-note")).toHaveText("Gespeichert.");
    await page.getByRole("button").filter({ hasText: "Schließen" }).click();
    const hideRow = page.locator(`[data-testid="song-admin-row"][data-title="${TAG}-song9"]`);
    await hideRow.getByTestId("song-toggle").click();
    await expect(hideRow.getByTestId("status-pill")).toHaveText("Ausgeblendet");
    created.songs.push(...((await call("GET", `/admin/medien/songs?q=${TAG}&page_size=50`, adminToken)).json.items as { id: string }[]).map((s) => s.id));
    expect(created.songs.length).toBe(9);
    // an official playlist with three songs in a chosen order
    await page.getByTestId("playlist-new").click();
    const pd = page.getByTestId("playlist-dialog");
    await pd.getByTestId("playlist-name").fill(`${TAG} Offiziell`);
    for (const n of ["song2", "song3", "song4"]) await pd.getByTestId("playlist-candidates").getByText(`${TAG}-${n}`, { exact: true }).click();
    await pd.getByTestId("playlist-members").locator("li").nth(2).getByLabel("Nach oben").click();
    await page.getByTestId("playlist-save").click();
    await expect(page.getByTestId("playlist-note")).toHaveText("Gespeichert.");
    await page.getByRole("button").filter({ hasText: "Schließen" }).click();
    created.playlists.push(...((await call("GET", "/admin/medien/playlists", adminToken)).json as { id: string; name: string }[]).filter((p) => p.name.startsWith(TAG)).map((p) => p.id));
    expect(created.playlists.length).toBe(1);
  });

  test("student: Musik, global player keeps playing on other pages, controls, favorites, playlists, reload restore", async ({ page }) => {
    await studentLogin(page, student);
    await page.goto("/medien/musik");
    await page.getByTestId("song-search").fill(TAG);
    await expect(page.getByTestId("song-row").first()).toBeVisible({ timeout: 20_000 });
    const rows = page.getByTestId("song-row");
    await expect(rows).toHaveCount(8); // the hidden one is not listed
    await expect(page.getByTestId("player-bar")).toHaveCount(0);

    // play the first one: the large vinyl player opens and the audio really runs; minimised, the bottom bar of the Musik page shows
    await rows.first().getByTestId("song-play").click();
    await expect(page.getByTestId("vinyl-player")).toBeVisible();
    await page.getByTestId("vinyl-minimize").click();
    const bar = page.getByTestId("player-bar");
    await expect(bar).toBeVisible();
    const title = await bar.getByTestId("player-title").textContent();
    await expect.poll(() => page.evaluate(() => (document.querySelector("audio") as HTMLAudioElement).currentTime), { timeout: 20_000 }).toBeGreaterThan(0.8);
    await page.evaluate(() => { (window as unknown as { __audio: Element }).__audio = document.querySelector('[data-testid="global-audio"]')!; });

    // background playback: client-side navigation to other student pages — same element, still playing, time keeps running
    for (const path of ["/medien/bibliothek", "/kurse", "/dashboard", "/medien"]) {
      const before = await page.evaluate(() => (document.querySelector("audio") as HTMLAudioElement).currentTime);
      await page.evaluate((p) => { const a = Array.from(document.querySelectorAll("a")).find((x) => x.getAttribute("href") === p); if (a) (a as HTMLAnchorElement).click(); else window.history.pushState({}, "", p); }, path);
      await page.waitForTimeout(1200);
      const state = await page.evaluate(() => { const a = document.querySelector("audio") as HTMLAudioElement; return { paused: a.paused, ended: a.ended, src: a.src.slice(-40), url: location.pathname, dur: a.duration, t: a.currentTime, same: (window as unknown as { __audio: Element }).__audio === document.querySelector('[data-testid="global-audio"]') }; });
      expect(state.same, `audio element recreated on ${path}`).toBe(true);
      expect(state.paused, `paused on ${path}: ${JSON.stringify(state)} before=${before}`).toBe(false);
      expect(state.t).toBeGreaterThan(before);
      await expect(page.getByTestId("floating-vinyl")).toBeVisible(); // other pages: the floating vinyl disc (medien-vinyl-player.spec.ts)
    }
    await page.getByTestId("medien-card-music").click(); // still no reload: the same player keeps going
    await expect(page).toHaveURL(/\/medien\/musik/);
    await page.waitForTimeout(1200);
    await search(page, "song-search", TAG, "song-row", 8);

    // controls: pause / play, seek, mute, volume, shuffle, repeat, next / previous, queue
    await bar.getByTestId("player-play").click();
    await expect.poll(() => page.evaluate(() => (document.querySelector("audio") as HTMLAudioElement).paused)).toBe(true);
    await bar.getByTestId("player-play").click();
    await expect.poll(() => page.evaluate(() => (document.querySelector("audio") as HTMLAudioElement).paused)).toBe(false);
    await bar.getByTestId("player-progress").fill("6");
    await expect.poll(() => page.evaluate(() => (document.querySelector("audio") as HTMLAudioElement).currentTime)).toBeGreaterThan(5.5);
    await bar.getByTestId("player-mute").click();
    expect(await page.evaluate(() => (document.querySelector("audio") as HTMLAudioElement).muted)).toBe(true);
    await bar.getByTestId("player-mute").click();
    expect(await page.evaluate(() => (document.querySelector("audio") as HTMLAudioElement).muted)).toBe(false);
    await bar.getByTestId("player-volume").fill("0.3");
    expect(await page.evaluate(() => (document.querySelector("audio") as HTMLAudioElement).volume)).toBeCloseTo(0.3, 1);
    await bar.getByTestId("player-shuffle").click();
    await expect(bar.getByTestId("player-shuffle")).toHaveAttribute("aria-pressed", "true");
    await bar.getByTestId("player-shuffle").click();
    await bar.getByTestId("player-repeat").click();
    await expect(bar.getByTestId("player-repeat")).toHaveAttribute("data-mode", "all");
    await bar.getByTestId("player-repeat").click();
    await expect(bar.getByTestId("player-repeat")).toHaveAttribute("data-mode", "one");
    await bar.getByTestId("player-repeat").click();
    await bar.getByTestId("player-next").click();
    await expect(bar.getByTestId("player-title")).not.toHaveText(title!);
    await bar.getByTestId("player-queue-toggle").click();
    await expect(page.getByTestId("player-queue-item")).toHaveCount(8);
    await page.getByTestId("player-queue-item").nth(3).click();
    await expect(bar.getByTestId("player-title")).toHaveText(new RegExp(`${TAG}-song`));
    await bar.getByTestId("player-queue-toggle").click();
    await bar.getByTestId("player-prev").click(); // within 3 s: back to the previous song
    await expect(bar.getByTestId("player-play")).toBeVisible();

    // favorites: heart on a row, own tab, remove
    // the list is sorted by popularity: it re-orders when a play is counted, so the song is followed by its title, not by its position
    const favTitle = (await rows.nth(1).getByTestId("song-title").textContent())!;
    const row = rows.filter({ hasText: favTitle });
    await row.getByTestId("song-favorite").click();
    await expect(row.getByTestId("song-favorite")).toHaveAttribute("aria-pressed", "true");
    await page.getByTestId("musik-tab-favorites").click();
    await expect(page.getByTestId("song-row")).toHaveCount(1);
    await expect(page.getByTestId("song-row").first()).toContainText(favTitle);
    await page.getByTestId("song-favorite").first().click();
    await expect(page.getByTestId("medien-empty")).toBeVisible();

    // own playlist: create, add songs, reorder, remove, play, official playlist is visible but read-only
    await page.getByTestId("musik-tab-playlists").click();
    await page.getByTestId("playlist-create-input").fill(`${TAG} Meine`);
    await page.getByTestId("playlist-create").click();
    await expect(page.getByTestId("playlist-title")).toHaveText(`${TAG} Meine`);
    await page.getByTestId("musik-tab-discover").click();
    await page.getByTestId("song-search").fill(TAG);
    for (const i of [0, 1, 2]) {
      await page.getByTestId("song-row").nth(i).getByTestId("song-add-playlist").click();
      await page.getByTestId("playlist-menu-item").filter({ hasText: `${TAG} Meine` }).click();
    }
    await page.getByTestId("musik-tab-playlists").click();
    await page.locator(`[data-testid="playlist-card"]`, { hasText: `${TAG} Meine` }).click();
    await expect(page.getByTestId("playlist-detail").getByTestId("song-row")).toHaveCount(3);
    const order = async () => page.getByTestId("playlist-detail").getByTestId("song-title").allTextContents();
    const before = await order();
    await page.getByTestId("playlist-detail").getByTestId("song-row").nth(2).getByTestId("song-up").click();
    await expect.poll(order).toEqual([before[0], before[2], before[1]]);
    await page.getByTestId("playlist-detail").getByTestId("song-row").nth(0).getByTestId("song-remove").click();
    await expect(page.getByTestId("playlist-detail").getByTestId("song-row")).toHaveCount(2);
    await page.getByTestId("playlist-play").click();
    await expect(page.getByTestId("vinyl-title")).toHaveText(before[2]);
    await page.getByTestId("vinyl-minimize").click();
    await expect(bar.getByTestId("player-title")).toHaveText(before[2]);
    await page.getByTestId("playlist-rename").click();
    await page.getByTestId("playlist-rename-input").fill(`${TAG} Umbenannt`);
    await page.getByTestId("playlist-rename-save").click();
    await expect(page.getByTestId("playlist-title")).toHaveText(`${TAG} Umbenannt`);
    await page.locator(`[data-testid="playlist-card"][data-official="1"]`, { hasText: `${TAG} Offiziell` }).click();
    await expect(page.getByTestId("playlist-detail").getByTestId("song-row")).toHaveCount(3);
    await expect(page.getByTestId("playlist-rename")).toHaveCount(0);
    await expect(page.getByTestId("playlist-delete")).toHaveCount(0);
    await page.locator(`[data-testid="playlist-card"]`, { hasText: `${TAG} Umbenannt` }).click();
    await page.getByTestId("playlist-delete").click();
    await expect(page.locator(`[data-testid="playlist-card"]`, { hasText: `${TAG} Umbenannt` })).toHaveCount(0);

    // history lists what was played
    await page.getByTestId("musik-tab-history").click();
    await expect(page.getByTestId("song-row").first()).toBeVisible();

    // reload: queue, song and position come back (paused), play continues from there
    const playingTitle = await bar.getByTestId("player-title").textContent();
    await page.getByTestId("player-progress").fill("5");
    await page.waitForTimeout(600);
    await page.reload();
    await expect(page.getByTestId("player-bar")).toBeVisible();
    await expect(page.getByTestId("player-title")).toHaveText(playingTitle!);
    expect(await page.evaluate(() => (document.querySelector("audio") as HTMLAudioElement).paused)).toBe(true);
    await expect(page.getByTestId("player-time")).not.toHaveText("0:00");
    await page.getByTestId("player-play").click();
    await expect.poll(() => page.evaluate(() => (document.querySelector("audio") as HTMLAudioElement).currentTime), { timeout: 20_000 }).toBeGreaterThan(4);
    await page.screenshot({ path: "test-results/medien-musik.png", fullPage: false });

    // a hidden song and the stream without a token are closed
    const hidden = (await call("GET", `/admin/medien/songs?q=${TAG}-song9`, adminToken)).json.items[0];
    const studentToken = await token(student, PASSWORD);
    expect((await call("POST", `/medien/songs/${hidden.id}/play`, studentToken)).status).toBe(404);
    expect((await fetch(`${API_URL}/api/v1/medien/stream/SONG/${hidden.id}`)).status).toBe(422);
  });

  test("admin: film with poster, chunked video upload, German + Uzbek subtitles; paid film", async ({ page }) => {
    await adminLogin(page);
    await page.goto("/admin/medien/filme");
    await expect(page.getByTestId("films-admin")).toBeVisible();
    for (const name of ["Deutsche Filme", "Kurzfilme", "Dokumentationen", "Lernvideos", "Serien", "Prüfungsvorbereitung", "Kinderfilme", "VIZU Originals"]) await expect(page.getByTestId("category-chip").filter({ hasText: name }).first()).toBeVisible();
    const make = async (title: string, opts: { paid?: boolean; offer?: boolean; withVideo?: boolean }) => {
      await page.getByTestId("film-new").click();
      const d = page.getByTestId("film-dialog");
      await fillField(d, "f-title", title);
      await d.getByTestId("f-description").fill(`Ein Film: ${title}`);
      await d.getByTestId("f-level").selectOption("B1");
      await fillField(d, "f-genre", "Drama");
      await d.getByTestId("f-category").selectOption({ label: "Kurzfilme" });
      await fillField(d, "f-year", "2019");
      await fillField(d, "f-minutes", "1");
      await d.getByTestId("f-status").selectOption("PUBLISHED");
      if (opts.paid) {
        await d.getByTestId("f-access").selectOption("PAID");
        await fillField(d, "f-price", "90000");
        await fillField(d, "f-old-price", "120000");
        if (opts.offer) await d.getByRole("checkbox", { name: "Sonderangebot" }).click();
      } else await d.getByRole("checkbox", { name: "Empfohlen" }).click();
      await d.getByTestId("film-poster-file").setInputFiles({ name: "poster.png", mimeType: "image/png", buffer: PNG });
      await page.getByTestId("film-save").click();
      await expect(page.getByTestId("film-note")).toHaveText("Gespeichert.", { timeout: 30_000 });
      if (opts.withVideo) {
        await expect(page.getByTestId("film-video-status")).toContainText("Kein Video");
        await d.getByTestId("film-video-file").setInputFiles(mp4Path());
        await page.getByTestId("film-video-upload").click();
        await expect(page.getByTestId("film-note")).toHaveText("Video hochgeladen und bereit.", { timeout: 60_000 });
        await expect(page.getByTestId("film-video-status")).toContainText("Bereit");
        await expect(page.getByTestId("section-info")).toBeVisible();
        await expect(page.getByTestId("section-video")).toBeVisible();
        await expect(page.getByTestId("section-subtitles")).toBeVisible();
        await expect(page.getByTestId("section-access")).toBeVisible();
        await d.getByTestId("sub-file-de").setInputFiles({ name: "de.srt", mimeType: "text/plain", buffer: Buffer.from(SRT) });
        await page.getByTestId("sub-upload-de").click();
        await expect(page.getByTestId("sub-status-de")).toContainText("Vorhanden", { timeout: 20_000 });
        await d.getByTestId("sub-file-uz").setInputFiles({ name: "uz.vtt", mimeType: "text/vtt", buffer: Buffer.from(VTT_UZ) });
        await page.getByTestId("sub-upload-uz").click();
        await expect(page.locator('[data-testid="film-subtitle"][data-present="1"]')).toHaveCount(2, { timeout: 20_000 });
        // a bad link / subtitle are refused
        await d.getByTestId("film-link").fill("http://unsicher.example/video.mp4");
        await page.getByTestId("film-link-save").click();
        await expect(page.getByTestId("film-note")).toContainText("https");
      }
      await page.getByTestId("film-close").click();
      await expect(page.getByTestId("film-dialog")).toHaveCount(0);
    };
    await make(`${TAG} Kurzfilm`, { withVideo: true });
    await make(`${TAG} Premiumfilm`, { paid: true, offer: true });
    await page.getByTestId("films-search").fill(TAG);
    const rows = page.getByTestId("film-row");
    await expect(rows).toHaveCount(2);
    await expect(rows.filter({ hasText: `${TAG} Kurzfilm` })).toContainText("Bereit");
    await expect(rows.filter({ hasText: `${TAG} Kurzfilm` })).toContainText("DE · UZ");
    await expect(rows.filter({ hasText: `${TAG} Premiumfilm` })).toContainText("90.000 UZS");
    created.films.push(...((await call("GET", `/admin/medien/films?q=${TAG}`, adminToken)).json.items as { id: string }[]).map((f) => f.id));
  });

  test("student: Filme hero, filters, player (speed, subtitles, fullscreen), continue watching, paid film locked", async ({ page }) => {
    await studentLogin(page, student);
    await page.goto("/medien/filme");
    await expect(page.getByTestId("film-hero")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByTestId("film-hero")).toContainText(`${TAG} Kurzfilm`);
    await expect(page.getByTestId("film-hero-watch")).toBeVisible();
    await expect(page.locator('[data-testid="film-row"]', { hasText: "Kurzfilme" })).toBeVisible();
    await page.getByTestId("film-search").fill(TAG);
    await expect(page.getByTestId("film-card")).toHaveCount(2);
    await page.getByTestId("film-access").selectOption("PAID");
    await expect(page.getByTestId("film-card")).toHaveCount(1);
    await page.getByTestId("film-access").selectOption("FREE");
    await expect(page.getByTestId("film-card")).toHaveCount(1);
    await page.getByTestId("film-level").selectOption("A1");
    await expect(page.getByTestId("medien-empty")).toBeVisible();
    await page.getByTestId("film-level").selectOption("B1");
    await page.getByTestId("film-length").selectOption("short");
    await expect(page.getByTestId("film-card")).toHaveCount(1);
    await page.getByTestId("film-length").selectOption("long");
    await expect(page.getByTestId("medien-empty")).toBeVisible();
    await page.getByTestId("film-length").selectOption("");
    await page.screenshot({ path: "test-results/medien-filme.png", fullPage: true });

    await page.getByTestId("film-card").first().click();
    await page.waitForTimeout(1200); // let the shared page transition finish (it remounts the page once)
    await expect(page.getByTestId("film-title")).toHaveText(`${TAG} Kurzfilm`);
    await expect(page.getByTestId("film-subtitle-langs")).toContainText("Deutsch");
    const player = page.getByTestId("film-player");
    await expect(player).toBeVisible();
    const video = player.getByTestId("film-video");
    await expect.poll(() => video.evaluate((v: HTMLVideoElement) => v.duration), { timeout: 30_000 }).toBeGreaterThan(4);
    await player.getByTestId("film-play").click();
    await expect.poll(() => video.evaluate((v: HTMLVideoElement) => v.currentTime), { timeout: 20_000 }).toBeGreaterThan(0.8);
    // German subtitles are on by default and clickable word by word; switch to Uzbek, then off
    await expect(player.getByTestId("film-cue")).toContainText("Guten Tag Welt", { timeout: 15_000 });
    await expect(player.getByTestId("film-cue")).toHaveAttribute("data-language", "de");
    const word = await player.getByTestId("film-cue").locator("[data-word]").first().evaluate((el) => {
      return new Promise<string>((resolve) => { window.addEventListener("medien:subtitle-word", (e) => resolve((e as CustomEvent).detail.word), { once: true }); (el as HTMLElement).click(); });
    });
    expect(word).toBe("Guten");
    await expect(page.getByTestId("word-popup")).toBeVisible(); // the word card opens (and the video pauses while it is open)
    await player.getByTestId("wp-close").click();
    await expect(page.getByTestId("word-popup")).toHaveCount(0);
    await player.getByTestId("film-subtitles").click();
    await expect(player.getByTestId("film-subtitle-option")).toHaveCount(2);
    await player.getByTestId("film-subtitle-option").filter({ hasText: "O'zbekcha" }).click();
    await video.evaluate((v: HTMLVideoElement) => { v.currentTime = 1; });
    await expect(player.getByTestId("film-cue")).toContainText("Salom dunyo", { timeout: 10_000 });
    await player.getByTestId("film-subtitles").click();
    await player.getByTestId("film-subtitle-off").click();
    await expect(player.getByTestId("film-cue")).toHaveCount(0);
    // speed, volume, mute, fullscreen control
    await player.getByTestId("film-speed").click();
    await expect(player.getByTestId("film-speed-option")).toHaveCount(6);
    await player.getByTestId("film-speed-option").filter({ hasText: "1.5×" }).click();
    expect(await video.evaluate((v: HTMLVideoElement) => v.playbackRate)).toBe(1.5);
    await player.getByTestId("film-mute").click();
    expect(await video.evaluate((v: HTMLVideoElement) => v.muted)).toBe(true);
    await player.getByTestId("film-mute").click();
    await expect(player.getByTestId("film-fullscreen")).toBeVisible();
    // Range: the browser seeks inside the file (the server answers 206)
    await video.evaluate((v: HTMLVideoElement) => { v.currentTime = 3.2; v.pause(); });
    await page.waitForTimeout(800);
    await page.getByRole("link", { name: "Filme" }).first().click().catch(() => undefined);
    // continue watching: leave at ~3 s, come back -> resumes there, and the film is on the "Weiter ansehen" row
    const filmUrl = page.url().includes("/medien/filme/") ? page.url() : "";
    await page.goto("/medien/filme");
    await expect(page.getByTestId("film-continue")).toContainText(`${TAG} Kurzfilm`, { timeout: 20_000 });
    await page.getByTestId("continue-film").first().click();
    await page.waitForTimeout(1200); // let the shared page transition finish (it remounts the page once)
    const resumed = page.getByTestId("film-player").getByTestId("film-video");
    await expect.poll(() => resumed.evaluate((v: HTMLVideoElement) => v.currentTime), { timeout: 30_000 }).toBeGreaterThan(2.5);
    void filmUrl;

    // the paid film: poster, text and price, no player and no stream
    await page.goto("/medien/filme");
    await page.getByTestId("film-search").fill(`${TAG} Premiumfilm`);
    await page.getByTestId("film-card").first().click();
    await page.waitForTimeout(1200); // let the shared page transition finish (it remounts the page once)
    await expect(page.getByTestId("film-poster")).toBeVisible();
    await expect(page.getByTestId("film-player")).toHaveCount(0);
    await expect(page.getByTestId("purchase-button")).toBeVisible();
    const studentToken = await token(student, PASSWORD);
    const film = ((await call("GET", `/medien/films?q=${TAG}%20Premiumfilm`, studentToken)).json.items as { id: string }[])[0];
    expect((await call("POST", `/medien/films/${film.id}/watch`, studentToken)).status).toBe(403);
    expect((await call("PUT", `/medien/progress/FILM/${film.id}`, studentToken, { position: 5, total: 60 })).status).toBe(403);
    const free = ((await call("GET", `/medien/films?q=${TAG}%20Kurzfilm`, studentToken)).json.items as { id: string }[])[0];
    const watch = (await call("POST", `/medien/films/${free.id}/watch`, studentToken)).json;
    const ranged = await fetch(`${API_URL}${watch.source.url}`, { headers: { Range: "bytes=0-99" } });
    expect([ranged.status, (await ranged.arrayBuffer()).byteLength]).toEqual([206, 100]);
    // the signed URL of another film does not work for this one
    expect((await fetch(`${API_URL}/api/v1/medien/stream/FILM/${film.id}?token=${watch.source.url.split("token=")[1]}`)).status).toBe(403);
  });
});

test.describe("Medienwelt on a phone", () => {
  test.skip(({ isMobile }) => !isMobile, "phone layout");
  test("pages fit the screen, the bookshelf only scrolls down, the player bar fits and plays", async ({ page }) => {
    const phoneDir = mkdtempSync(join(tmpdir(), "medien-phone-")); // its own folder: the desktop run removes `work` when it is done
    const admin = await token(ADMIN.email, ADMIN.password);
    const form = new FormData();
    form.append("file", new Blob([readFileSync(mp3(`${TAG}-mobile.mp3`, 30, phoneDir))], { type: "audio/mpeg" }), `${TAG}-mobile.mp3`);
    form.append("title", `${TAG}-mobile`); form.append("artist", "VIZU Band"); form.append("status", "PUBLISHED");
    const made = await fetch(`${API_URL}/api/v1/admin/medien/songs`, { method: "POST", headers: { Authorization: `Bearer ${admin}` }, body: form });
    expect(made.status, await made.clone().text()).toBe(200);
    const songId = (await made.json()).id as string;
    try {
      const student = await createStudent();
      await studentLogin(page, student);
      for (const path of ["/medien", "/medien/bibliothek", "/medien/musik", "/medien/filme"]) {
        await page.goto(path);
        await expect(page.locator("main")).toBeVisible();
        await page.waitForTimeout(600);
        await noHorizontalScroll(page);
      }
      await page.goto("/medien/bibliothek");
      await page.screenshot({ path: "test-results/medien-bibliothek-mobile.png", fullPage: false });
      await page.goto("/medien/musik");
      await page.getByTestId("song-search").fill(`${TAG}-mobile`);
      await page.getByTestId("song-play").first().click();
      await expect(page.getByTestId("vinyl-player")).toBeVisible();
      await page.getByTestId("vinyl-minimize").click();
      await expect(page.getByTestId("player-bar")).toBeVisible();
      await expect.poll(() => page.evaluate(() => (document.querySelector("audio") as HTMLAudioElement).currentTime), { timeout: 20_000 }).toBeGreaterThan(0.5);
      await noHorizontalScroll(page);
      for (const id of ["player-prev", "player-play", "player-next", "player-progress", "player-favorite", "player-queue-toggle"]) await expect(page.getByTestId(id)).toBeVisible();
      const box = await page.getByTestId("player-bar").boundingBox();
      expect(box!.width).toBeLessThanOrEqual(page.viewportSize()!.width + 1);
      await page.getByTestId("player-play").click(); // pause / resume works by touch targets
      await expect.poll(() => page.evaluate(() => (document.querySelector("audio") as HTMLAudioElement).paused)).toBe(true);
      await page.getByTestId("player-play").click();
      await expect.poll(() => page.evaluate(() => (document.querySelector("audio") as HTMLAudioElement).paused)).toBe(false);
      // still playing after moving to another page
      await page.evaluate(() => { (Array.from(document.querySelectorAll("a")).find((a) => a.getAttribute("href") === "/medien") as HTMLAnchorElement | undefined)?.click(); });
      await page.waitForTimeout(1000);
      expect(await page.evaluate(() => (document.querySelector("audio") as HTMLAudioElement).paused)).toBe(false);
      await page.screenshot({ path: "test-results/medien-player-mobile.png", fullPage: false });
    } finally {
      await fetch(`${API_URL}/api/v1/admin/medien/songs/${songId}`, { method: "DELETE", headers: { Authorization: `Bearer ${admin}` } });
      rmSync(phoneDir, { recursive: true, force: true });
    }
  });
});