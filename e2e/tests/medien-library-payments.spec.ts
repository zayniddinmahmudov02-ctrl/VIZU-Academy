import { readFileSync } from "node:fs";
import { deflateSync } from "node:zlib";

import { expect, test, type Page } from "@playwright/test";

import { ADMIN, API_URL, PASSWORD, createStudent, loginViaForm } from "./helpers";

// VIZU MEDIENWELT · Bibliothek: the PDF reader (continuous scroll / book mode, zoom, fullscreen, resume), the free preview of a paid book (the server
// delivers only the free pages), the manual card payment (receipt or transfer time), the Super Admin's approval, the full book and the PDF download.
// Real backend, real database, real files — local stack only. Everything created here is removed again through the admin API.
const TAG = `L${Date.now().toString(36)}${Math.random().toString(36).slice(2, 5)}`;
const CARD = "9860 0401 1406 3742";

/** A real PDF: every page carries the uncompressed text `Seite <n>` (so a test can prove which pages a delivered file contains). */
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

/** A small, valid PNG (a receipt photo): the server decodes and re-encodes receipts, so a truncated fixture would be refused. */
function png(w = 64, h = 48): Buffer {
  const crc32 = (buf: Buffer) => {
    let crc = 0xffffffff;
    for (const byte of buf) {
      crc ^= byte;
      for (let k = 0; k < 8; k += 1) crc = crc & 1 ? (crc >>> 1) ^ 0xedb88320 : crc >>> 1;
    }
    return (crc ^ 0xffffffff) >>> 0;
  };
  const chunk = (type: string, data: Buffer) => {
    const body = Buffer.concat([Buffer.from(type, "ascii"), data]);
    const len = Buffer.alloc(4); len.writeUInt32BE(data.length);
    const crc = Buffer.alloc(4); crc.writeUInt32BE(crc32(body));
    return Buffer.concat([len, body, crc]);
  };
  const header = Buffer.alloc(13); header.writeUInt32BE(w, 0); header.writeUInt32BE(h, 4); header[8] = 8; header[9] = 2;
  const rows = Buffer.alloc((w * 3 + 1) * h);
  for (let y = 0; y < h; y += 1) for (let x = 0; x < w; x += 1) { const o = y * (w * 3 + 1) + 1 + x * 3; rows[o] = (x * 4) & 255; rows[o + 1] = (y * 5) & 255; rows[o + 2] = 150; }
  return Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), chunk("IHDR", header), chunk("IDAT", deflateSync(rows)), chunk("IEND", Buffer.alloc(0))]);
}

async function token(email: string, password: string) {
  const res = await fetch(`${API_URL}/api/v1/auth/login`, { method: "POST", headers: { "Content-Type": "application/json", "X-Forwarded-For": `10.98.${Math.floor(Math.random() * 250)}.${Math.floor(Math.random() * 250)}` }, body: JSON.stringify({ identifier: email, password }) });
  expect(res.status, await res.clone().text()).toBe(200);
  return (await res.json()).access_token as string;
}
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Json = any;
const call = async (method: string, url: string, bearer: string | null, body?: unknown): Promise<{ status: number; json: Json; headers: Headers }> => {
  const res = await fetch(`${API_URL}/api/v1${url}`, { method, headers: { ...(bearer ? { Authorization: `Bearer ${bearer}` } : {}), ...(body ? { "Content-Type": "application/json" } : {}) }, body: body ? JSON.stringify(body) : undefined });
  const text = await res.text();
  return { status: res.status, json: text && res.headers.get("content-type")?.includes("json") ? JSON.parse(text) : null, headers: res.headers };
};

/** A published book with a real PDF, made through the admin API. */
async function makeBook(admin: string, title: string, opts: { paid?: boolean; pages: number; preview?: number }) {
  const made = await call("POST", "/admin/medien/books", admin, { title, author: "E2E Autor", language: "de", level: "A2", status: "PUBLISHED", ...(opts.paid ? { access_type: "PAID", price: 45000 } : {}), ...(opts.preview !== undefined ? { preview_pages_count: opts.preview } : {}) });
  expect(made.status, JSON.stringify(made.json)).toBe(200);
  const form = new FormData();
  form.append("file", new Blob([new Uint8Array(pdf(opts.pages))], { type: "application/pdf" }), "buch.pdf");
  const res = await fetch(`${API_URL}/api/v1/admin/medien/books/${made.json.id}/file`, { method: "POST", headers: { Authorization: `Bearer ${admin}` }, body: form });
  expect(res.status, await res.clone().text()).toBe(200);
  return (await res.json()) as { id: string; title: string; page_count: number };
}

async function adminLogin(page: Page) {
  await page.addInitScript(() => localStorage.setItem("vizu-language", JSON.stringify({ state: { language: "de" }, version: 0 })));
  await loginViaForm(page, ADMIN.email, ADMIN.password);
  await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
  await page.getByRole("button", { name: "Bestätigen" }).click();
  await expect(page).toHaveURL(/\/admin/);
}
async function studentLogin(page: Page, email: string) {
  await loginViaForm(page, email, PASSWORD);
  await expect(page).toHaveURL(/\/dashboard/);
  await page.evaluate(() => localStorage.setItem("vizu-language", JSON.stringify({ state: { language: "uz" }, version: 0 })));
  await page.reload();
}
const noHorizontalScroll = async (page: Page) => expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
const tashkentDay = (offsetHours = 0) => new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Tashkent" }).format(new Date(Date.now() + offsetHours * 3600_000));
const text = (buf: Buffer) => buf.toString("latin1");

// ---------------------------------------------------------------------------------------------------------------------------------------------------
test.describe.serial("Bibliothek (desktop): preview, payment, approval, download, reading position", () => {
  test.skip(({ isMobile }) => isMobile, "the phone has its own describe below");
  test.use({ permissions: ["clipboard-read", "clipboard-write"] });
  let admin = "";
  let studentA = "";
  let studentB = "";
  let tokenA = "";
  let tokenB = "";
  let paid = { id: "", title: "" };
  let second = { id: "", title: "" };
  let free = { id: "", title: "" };
  let requestA = "";
  const made: string[] = [];

  test.beforeAll(async () => {
    admin = await token(ADMIN.email, ADMIN.password);
    studentA = await createStudent();
    studentB = await createStudent();
    tokenA = await token(studentA, PASSWORD);
    tokenB = await token(studentB, PASSWORD);
    paid = await makeBook(admin, `${TAG} Paid`, { paid: true, pages: 15 });
    second = await makeBook(admin, `${TAG} Second`, { paid: true, pages: 15 });
    free = await makeBook(admin, `${TAG} Free`, { pages: 15 });
    made.push(paid.id, second.id, free.id);
  });

  test.afterAll(async () => {
    for (const id of made) await call("DELETE", `/admin/medien/books/${id}`, admin);
  });

  test("security: the payment and the reader API are closed to anonymous users and to students where they must be", async () => {
    for (const [method, url] of [["GET", "/medien/book-payment-info"], ["GET", "/medien/book-payments/mine"], ["POST", `/medien/books/${paid.id}/open`], ["POST", `/medien/books/${paid.id}/download-link`], ["POST", `/medien/books/${paid.id}/payment-requests`]] as const) {
      expect((await call(method, url, null)).status, `${method} ${url}`).toBe(401);
    }
    expect((await fetch(`${API_URL}/api/v1/medien/download/book/${paid.id}`)).status).toBe(422); // a token is required
    expect((await fetch(`${API_URL}/api/v1/medien/download/book/${paid.id}?token=garbage`)).status).toBe(401);
    for (const [method, url] of [["GET", "/admin/medien/book-payments"], ["GET", "/admin/medien/book-payments/00000000-0000-0000-0000-000000000000"], ["POST", "/admin/medien/book-payments/00000000-0000-0000-0000-000000000000/decision"], ["PUT", "/admin/medien/book-payment-settings"]] as const) {
      expect((await call(method, url, null, method === "GET" ? undefined : { status: "APPROVED" })).status, `anonymous ${method} ${url}`).toBe(401);
      expect((await call(method, url, tokenA, method === "GET" ? undefined : { status: "APPROVED" })).status, `student ${method} ${url}`).toBe(403);
    }
    // the price is the book's, whatever the client says; nothing is stored without a receipt or a transfer time
    const form = new FormData();
    form.append("amount", "1");
    form.append("price", "1");
    const refused = await fetch(`${API_URL}/api/v1/medien/books/${paid.id}/payment-requests`, { method: "POST", headers: { Authorization: `Bearer ${tokenB}` }, body: form });
    expect(refused.status).toBe(422);
    expect((await call("GET", "/medien/book-payments/mine", tokenB)).json).toEqual([]);
  });

  test("admin: free preview pages per book, the payment card (UI) — a bad card number is refused", async ({ page }) => {
    await adminLogin(page);
    await page.goto("/admin/medien/bibliothek");
    await page.getByTestId("books-search").fill(`${TAG} Paid`);
    await page.getByTestId("book-row").filter({ hasText: `${TAG} Paid` }).getByTestId("book-edit").click();
    const dialog = page.getByTestId("book-dialog");
    await expect(dialog.getByTestId("f-preview-pages")).toHaveValue("10"); // the default
    await dialog.getByTestId("f-preview-pages").fill("600");
    await page.getByTestId("book-save").click();
    await expect(page.getByTestId("book-note")).toContainText("0 und 500");
    await dialog.getByTestId("f-preview-pages").fill("10");
    await page.getByTestId("book-save").click();
    await expect(page.getByTestId("book-note")).toHaveText("Gespeichert.", { timeout: 30_000 });
    await page.getByTestId("book-close").click();
    await expect(page.getByTestId("book-row").filter({ hasText: `${TAG} Paid` })).toContainText("Leseprobe: 10 Seiten");

    await page.getByTestId("books-tab-payments").click();
    await page.getByTestId("card-number").fill("12345");
    await page.getByTestId("card-save").click();
    await expect(page.getByTestId("card-message")).toContainText("16 bis 19 Ziffern");
    await page.getByTestId("card-number").fill(CARD);
    await page.getByTestId("card-holder").fill("VIZU E2E");
    await page.getByTestId("card-save").click();
    await expect(page.getByTestId("card-message")).toHaveText("Kartendaten gespeichert.");
    expect((await call("GET", "/medien/book-payment-info", tokenA)).json).toMatchObject({ card_number: CARD.replace(/\s/g, ""), card_holder: "VIZU E2E", configured: true });
  });

  test("student: a paid book shows only the free pages — the server never sends page 11 — and the paywall opens at page 11", async ({ page }) => {
    // what is delivered: the first 10 pages, not the original, no download
    const opened = await call("POST", `/medien/books/${paid.id}/open`, tokenA);
    expect([opened.status, opened.json.mode, opened.json.preview_pages, opened.json.total_pages, opened.json.can_download]).toEqual([200, "preview", 10, 15, false]);
    const delivered = Buffer.from(await (await fetch(`${API_URL}${opened.json.url}`)).arrayBuffer());
    expect(text(delivered)).toContain("Seite 10");
    expect(text(delivered)).not.toContain("Seite 11");
    expect(text(delivered)).not.toContain("Seite 15");
    expect(delivered.length).toBeLessThan(pdf(15).length);
    expect((await call("POST", `/medien/books/${paid.id}/download-link`, tokenA)).status).toBe(403);
    const previewToken = new URL(opened.json.url, API_URL).searchParams.get("token");
    expect((await fetch(`${API_URL}/api/v1/medien/download/book/${paid.id}?token=${previewToken}`)).status).toBe(403);
    expect((await fetch(`${API_URL}/api/v1/medien/stream/BOOK/${second.id}?token=${previewToken}`)).status).toBe(403); // a token belongs to one book

    await studentLogin(page, studentA);
    await page.goto(`/medien/bibliothek/${paid.id}`);
    await expect(page.getByTestId("book-title")).toHaveText(paid.title);
    await expect(page.getByTestId("book-read")).toHaveCount(0);
    await expect(page.getByTestId("book-download")).toHaveCount(0);
    await expect(page.getByTestId("book-preview")).toContainText("10");
    await page.getByTestId("book-preview").click();
    const reader = page.getByTestId("pdf-reader");
    await expect(reader.getByTestId("reader-canvas").first()).toBeVisible({ timeout: 30_000 });
    await expect(reader).toHaveAttribute("data-mode", "book"); // the default everywhere: one page at a time, turned like a book
    await expect(reader.getByTestId("reader-preview-badge")).toContainText("10");
    await expect(reader.getByTestId("reader-total")).toHaveText("/ 15");
    await expect(reader.getByTestId("book-download")).toHaveCount(0);
    // page 10 is the last free page; "next" there asks for the purchase
    await reader.getByTestId("reader-page").fill("10");
    await reader.getByTestId("reader-page").press("Enter");
    await expect(reader.getByTestId("reader-page")).toHaveValue("10");
    await expect(reader.getByTestId("reader-paywall")).toHaveCount(0);
    await reader.getByTestId("reader-next").click();
    const paywall = reader.getByTestId("reader-paywall");
    await expect(paywall).toBeVisible();
    await expect(paywall).toContainText("Das vollständige Buch freischalten!");
    await expect(paywall).toContainText("Ushbu kitobning dastlabki 10 sahifasini bepul o‘qishingiz mumkin. Kitobning to‘liq versiyasidan foydalanish uchun uni xarid qiling.");
    await expect(paywall.getByTestId("paywall-buy")).toHaveText("Jetzt kaufen — Xarid qilish");
    await expect(paywall.getByTestId("paywall-back")).toHaveText("Zurück — Ortga qaytish");
    await paywall.getByTestId("paywall-back").click();
    await expect(paywall).toHaveCount(0);
    await expect(reader.getByTestId("reader-page")).toHaveValue("10"); // stays on the last free page
    // typing page 11 or any later page asks for the purchase too
    await reader.getByTestId("reader-page").fill("11");
    await reader.getByTestId("reader-page").press("Enter");
    await expect(paywall).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(paywall).toHaveCount(0);
    await reader.getByTestId("reader-page").fill("999");
    await reader.getByTestId("reader-page").press("Enter");
    await expect(paywall).toBeVisible();
    await paywall.getByTestId("paywall-back").click();
    // continuous mode: ten pages and a locked "page 11"; scrolling to the end asks for the purchase
    await reader.getByTestId("reader-mode").click();
    await expect(reader).toHaveAttribute("data-mode", "scroll");
    await expect(reader.getByTestId("reader-page-view")).toHaveCount(10);
    await expect(reader.getByTestId("reader-locked-page")).toBeVisible();
    await reader.getByTestId("reader-scroll").evaluate((el) => { el.scrollTop = el.scrollHeight; });
    await expect(paywall).toBeVisible();
    // "Jetzt kaufen" leaves the reader and opens the payment window
    await paywall.getByTestId("paywall-buy").click();
    await expect(page.getByTestId("pdf-reader")).toHaveCount(0);
    await expect(page.getByTestId("book-payment-modal")).toBeVisible();
    await expect(page.getByTestId("pay-book-title")).toHaveText(paid.title);
  });

  test("student: the payment window — card, copy, instruction, validation, receipt", async ({ page }) => {
    await studentLogin(page, studentA);
    await page.goto(`/medien/bibliothek/${paid.id}`);
    await page.getByTestId("book-buy").click();
    const modal = page.getByTestId("book-payment-modal");
    await expect(modal.getByTestId("pay-book-price")).toContainText("45.000");
    await expect(modal.getByTestId("pay-card-number")).toHaveText(CARD);
    await expect(modal.getByTestId("pay-card-holder")).toHaveText("VIZU E2E");
    await expect(modal.getByTestId("pay-instruction")).toContainText("Kitobni xarid qilish uchun ko‘rsatilgan karta raqamiga kerakli summani o'tkazing.");
    await expect(modal.getByTestId("pay-instruction")).toContainText("Admin to‘lovni tekshirib, tasdiqlaganidan keyin kitob siz uchun to‘liq ochiladi.");
    await modal.getByTestId("pay-copy").click();
    await expect.poll(() => page.evaluate(() => navigator.clipboard.readText())).toBe(CARD.replace(/\s/g, ""));
    // the amount is shown, never editable: the server takes the book's price
    await expect(modal.getByTestId("pay-amount")).toHaveAttribute("readonly", "");
    await expect(modal.getByTestId("pay-amount")).toHaveValue(/45\.000/);

    // variant A (receipt): nothing chosen / wrong type / too big
    await modal.getByTestId("pay-submit").click();
    await expect(modal.getByTestId("pay-error")).toContainText("Chekni yuklang");
    await modal.getByTestId("pay-receipt").setInputFiles({ name: "chek.txt", mimeType: "text/plain", buffer: Buffer.from("das ist kein beleg") });
    await expect(modal.getByTestId("pay-error")).toContainText("qo'llab-quvvatlanmaydi");
    await modal.getByTestId("pay-receipt").setInputFiles({ name: "chek.png", mimeType: "image/png", buffer: Buffer.alloc(9 * 1024 * 1024, 1) });
    await expect(modal.getByTestId("pay-error")).toContainText("8 MB");
    // variant B (no receipt): date AND time are mandatory, not in the future
    await modal.getByTestId("pay-variant-time").click();
    await modal.getByTestId("pay-time").fill("");
    await modal.getByTestId("pay-submit").click();
    await expect(modal.getByTestId("pay-error")).toContainText("sanasi va vaqtini");
    await modal.getByTestId("pay-date").fill(tashkentDay(30));
    await modal.getByTestId("pay-time").fill("10:00");
    await modal.getByTestId("pay-submit").click();
    await expect(modal.getByTestId("pay-error")).toContainText("kelajakda");
    expect((await call("GET", "/medien/book-payments/mine", tokenA)).json).toEqual([]); // nothing was stored
    // server side: the same rules (future, too old, no receipt and no time)
    const post = async (fields: Record<string, string>, who = tokenB) => {
      const form = new FormData();
      for (const [k, v] of Object.entries(fields)) form.append(k, v);
      const res = await fetch(`${API_URL}/api/v1/medien/books/${paid.id}/payment-requests`, { method: "POST", headers: { Authorization: `Bearer ${who}` }, body: form });
      return { status: res.status, json: await res.json().catch(() => null) as Json };
    };
    expect((await post({ no_receipt: "true", transfer_date: tashkentDay(30), transfer_time: "10:00" })).json.message).toContain("TRANSFER_IN_FUTURE");
    expect((await post({ no_receipt: "true", transfer_date: tashkentDay(-24 * 40), transfer_time: "10:00" })).json.message).toContain("TRANSFER_TOO_OLD");
    expect((await post({ no_receipt: "true" })).json.message).toContain("TRANSFER_TIME_REQUIRED");
    expect((await post({})).json.message).toContain("RECEIPT_OR_NO_RECEIPT");

    // variant A with a real receipt
    await modal.getByTestId("pay-variant-receipt").click();
    await modal.getByTestId("pay-receipt").setInputFiles({ name: "chek.png", mimeType: "image/png", buffer: png() });
    await expect(modal.getByTestId("pay-receipt-name")).toHaveText("chek.png");
    await modal.getByTestId("pay-note").fill("Chek ilova qilindi");
    await modal.getByTestId("pay-submit").click();
    await expect(modal.getByTestId("pay-pending")).toBeVisible();
    await modal.getByTestId("pay-done").click();

    const mine = (await call("GET", "/medien/book-payments/mine", tokenA)).json as Json[];
    expect(mine.length).toBe(1);
    expect(mine[0]).toMatchObject({ status: "PENDING", amount: 45000, has_receipt: true, no_receipt: false, book_id: paid.id });
    requestA = mine[0].id;
    // pending: the button says so, a second request is refused, and there is still no access
    await expect(page.getByTestId("book-buy")).toContainText("tekshirilmoqda");
    expect((await post({ no_receipt: "true", transfer_date: tashkentDay(-24), transfer_time: "10:00" }, tokenA)).json.message).toContain("PAYMENT_PENDING");
    expect((await call("POST", `/medien/books/${paid.id}/open`, tokenA)).json.mode).toBe("preview");
    expect((await call("POST", `/medien/books/${paid.id}/download-link`, tokenA)).status).toBe(403);
    // the receipt is private: its owner and the Super Admin only
    const own = await fetch(`${API_URL}/api/v1/medien/book-payments/${requestA}/receipt`, { headers: { Authorization: `Bearer ${tokenA}` } });
    expect([own.status, own.headers.get("content-type"), own.headers.get("x-content-type-options"), own.headers.get("cache-control")]).toEqual([200, "image/png", "nosniff", "private, no-store"]);
    expect((await fetch(`${API_URL}/api/v1/medien/book-payments/${requestA}/receipt`, { headers: { Authorization: `Bearer ${tokenB}` } })).status).toBe(404);
    expect((await fetch(`${API_URL}/api/v1/medien/book-payments/${requestA}/receipt`)).status).toBe(401);
    expect((await call("POST", `/medien/book-payments/${requestA}/cancel`, tokenB)).status).toBe(404); // another student's request does not exist for B
    // the student's own list shows the status
    await page.goto("/medien/bibliothek");
    await expect(page.getByTestId("my-payment-row").filter({ hasText: paid.title })).toContainText("Tekshirilmoqda");
  });

  test("admin: checks the receipt, rejects with a reason — the student sees it and asks again — admin approves — the full book is open", async ({ page, browser }) => {
    const adminPage = await (await browser.newContext()).newPage();
    await adminLogin(adminPage);
    await adminPage.goto("/admin/medien/bibliothek");
    await expect(adminPage.getByTestId("payments-pending-count")).toBeVisible();
    await adminPage.getByTestId("books-tab-payments").click();
    const row = adminPage.getByTestId("payment-row").filter({ hasText: studentA });
    await expect(row).toContainText(`${TAG} Paid`);
    await expect(row).toContainText("45.000 UZS");
    await expect(row).toContainText("Ja (PNG)");
    await row.getByTestId("payment-review").click();
    const dialog = adminPage.getByTestId("payment-dialog");
    await expect(dialog.getByTestId("payment-student")).toBeVisible();
    await expect(dialog.getByTestId("payment-book")).toHaveText(paid.title);
    await expect(dialog.getByTestId("payment-amount")).toContainText("45.000");
    await expect(dialog.getByTestId("payment-note")).toHaveText("Chek ilova qilindi");
    await expect(dialog.getByTestId("receipt-image")).toBeVisible();
    await expect.poll(() => dialog.getByTestId("receipt-image").evaluate((img: HTMLImageElement) => img.naturalWidth)).toBe(64);
    // a rejection needs a reason
    await expect(dialog.getByTestId("payment-reject")).toBeDisabled();
    await expect(dialog.getByTestId("payment-approve")).toBeDisabled();
    await dialog.getByTestId("payment-reason").fill("Summa mos kelmadi");
    await dialog.getByTestId("payment-reject").click();
    await expect(dialog.getByTestId("payment-message")).toContainText("abgelehnt");
    await expect(dialog.getByTestId("payment-decided")).toContainText("Abgelehnt");
    await adminPage.getByTestId("payment-close").click();

    // the student: still locked, sees the reason, can ask again
    await studentLogin(page, studentA);
    await page.goto(`/medien/bibliothek/${paid.id}`);
    await expect(page.getByTestId("book-payment-rejected")).toContainText("Rad etildi: Summa mos kelmadi");
    await expect(page.getByTestId("book-read")).toHaveCount(0);
    expect((await call("POST", `/medien/books/${paid.id}/open`, tokenA)).json.mode).toBe("preview");
    await expect(page.getByTestId("book-buy")).toContainText("Qayta xarid qilish");
    await page.getByTestId("book-buy").click();
    const modal = page.getByTestId("book-payment-modal");
    await modal.getByTestId("pay-variant-time").click();
    await modal.getByTestId("pay-date").fill(tashkentDay(-24));
    await modal.getByTestId("pay-time").fill("15:45");
    await modal.getByTestId("pay-submit").click();
    await expect(modal.getByTestId("pay-pending")).toBeVisible();
    await modal.getByTestId("pay-done").click();
    // uploading a receipt or a time never opens the book by itself
    expect((await call("POST", `/medien/books/${paid.id}/open`, tokenA)).json.mode).toBe("preview");

    // the second request: no receipt, the transfer time is shown for the check; approval needs the "checked" box
    await adminPage.reload();
    await adminPage.getByTestId("books-tab-payments").click();
    await adminPage.getByTestId("payments-filter-ALL").click();
    await expect(adminPage.getByTestId("payment-row").filter({ hasText: studentA })).toHaveCount(2);
    await adminPage.getByTestId("payments-filter-PENDING").click();
    const pending = adminPage.getByTestId("payment-row").filter({ hasText: studentA });
    await expect(pending).toHaveCount(1);
    await expect(pending).toContainText("Ohne Beleg");
    await pending.getByTestId("payment-review").click();
    const d2 = adminPage.getByTestId("payment-dialog");
    await expect(d2.getByTestId("receipt-none")).toContainText("15:45");
    await expect(d2.getByTestId("payment-history")).toContainText("Summa mos kelmadi");
    await expect(d2.getByTestId("payment-approve")).toBeDisabled();
    await d2.getByTestId("payment-verified").click();
    await d2.getByTestId("payment-approve").click();
    await expect(d2.getByTestId("payment-message")).toContainText("freigeschaltet");
    await expect(d2.getByTestId("payment-purchases")).toContainText(paid.title);
    // a decided request cannot be decided again — not approved twice, not rejected after approval
    const list = (await call("GET", `/admin/medien/book-payments?status=APPROVED&q=${TAG}`, admin)).json as Json;
    expect(list.items.length).toBe(1);
    const approvedId = list.items[0].id as string;
    expect((await call("POST", `/admin/medien/book-payments/${approvedId}/decision`, admin, { status: "APPROVED" })).status).toBe(409);
    expect((await call("POST", `/admin/medien/book-payments/${approvedId}/decision`, admin, { status: "REJECTED", note: "zu spaet" })).status).toBe(409);
    expect((await call("POST", `/admin/medien/book-payments/${approvedId}/decision`, tokenA, { status: "APPROVED" })).status).toBe(403);
    // one payment opens one book: the second paid book stays a preview
    expect((await call("POST", `/medien/books/${second.id}/open`, tokenA)).json.mode).toBe("preview");

    // the student: the whole book, no preview limit, a download, purchase history keeps the purchase
    await page.reload();
    await expect(page.getByTestId("book-read")).toBeVisible();
    await expect(page.getByTestId("book-buy")).toHaveCount(0);
    await expect(page.getByTestId("book-download")).toBeVisible();
    const full = await call("POST", `/medien/books/${paid.id}/open`, tokenA);
    expect([full.json.mode, full.json.preview_pages, full.json.total_pages, full.json.can_download]).toEqual(["full", null, 15, true]);
    await page.getByTestId("book-read").click();
    const reader = page.getByTestId("pdf-reader");
    await expect(reader.getByTestId("reader-canvas").first()).toBeVisible({ timeout: 30_000 });
    await expect(reader.getByTestId("reader-preview-badge")).toHaveCount(0);
    await reader.getByTestId("reader-page").fill("11");
    await reader.getByTestId("reader-page").press("Enter");
    await expect(reader.getByTestId("reader-page")).toHaveValue("11");
    await expect(reader.getByTestId("reader-paywall")).toHaveCount(0);
    await expect(reader.getByTestId("book-download")).toBeVisible();
    await reader.getByTestId("reader-close").click();
    await expect(page.getByTestId("my-payment-row")).toHaveCount(0); // (that list lives on the Bibliothek page)
    await page.goto("/medien/bibliothek");
    await expect(page.getByTestId("my-payment-row").filter({ hasText: paid.title })).toHaveCount(2);
    await expect(page.getByTestId("my-payment-row").filter({ hasText: "Tasdiqlangan" })).toHaveCount(1);
    await expect(page.getByTestId("my-payment-row").filter({ hasText: "Rad etilgan" })).toContainText("Summa mos kelmadi");
    await adminPage.context().close();
  });

  test("student: the PDF download — original file, file name from the title, only for the owner", async ({ page }) => {
    await studentLogin(page, studentA);
    await page.goto(`/medien/bibliothek/${paid.id}`);
    const [download] = await Promise.all([page.waitForEvent("download"), page.getByTestId("book-download").click()]);
    expect(download.suggestedFilename()).toBe(`${paid.title}.pdf`);
    const saved = readFileSync((await download.path())!);
    expect(saved.equals(pdf(15))).toBe(true); // the original, byte for byte
    // another student, anonymous callers and a stale token get nothing
    expect((await call("POST", `/medien/books/${paid.id}/download-link`, tokenB)).status).toBe(403);
    const link = (await call("POST", `/medien/books/${paid.id}/download-link`, tokenA)).json as { url: string; filename: string };
    expect(link.filename).toBe(`${paid.title}.pdf`);
    const fetched = await fetch(`${API_URL}${link.url}`);
    expect([fetched.status, fetched.headers.get("content-type"), fetched.headers.get("cache-control"), fetched.headers.get("content-disposition")?.includes("attachment")]).toEqual([200, "application/pdf", "private, no-store", true]);
    // free books download for everybody who is logged in
    expect((await call("POST", `/medien/books/${free.id}/download-link`, tokenB)).status).toBe(200);
    expect((await call("POST", `/medien/books/${free.id}/download-link`, null)).status).toBe(401);
    // after the admin revokes the purchase the same link is dead
    const purchases = (await call("GET", "/admin/medien/purchases?status=GRANTED", admin)).json as { id: string; user_email: string; content_id: string }[];
    const mineRow = purchases.find((p) => p.user_email === studentA && p.content_id === paid.id)!;
    expect((await call("POST", `/admin/medien/purchases/${mineRow.id}/decision`, admin, { status: "REVOKED" })).status).toBe(200);
    expect((await fetch(`${API_URL}${link.url}`)).status).toBe(403);
    expect((await call("POST", `/medien/books/${paid.id}/open`, tokenA)).json.mode).toBe("preview");
  });

  test("student: reading position is stored in the database and 'continue reading' resumes it (continuous and single page)", async ({ page }) => {
    await studentLogin(page, studentB);
    await page.goto(`/medien/bibliothek/${free.id}`);
    await expect(page.getByTestId("book-read")).toHaveText(/O'qish/);
    await page.getByTestId("book-read").click();
    const reader = page.getByTestId("pdf-reader");
    await expect(reader.getByTestId("reader-canvas").first()).toBeVisible({ timeout: 30_000 });
    await expect(reader.getByTestId("reader-total")).toHaveText("/ 15");
    await expect(reader.getByTestId("book-download")).toBeVisible(); // a free book downloads
    // continuous scroll: every page is laid out, only the near ones are drawn; page box and progress follow the scrolling
    await reader.getByTestId("reader-mode").click();
    await expect(reader).toHaveAttribute("data-mode", "scroll");
    await expect(reader.getByTestId("reader-page-view")).toHaveCount(15);
    await reader.getByTestId("reader-page").fill("7");
    await reader.getByTestId("reader-page").press("Enter");
    await expect(reader.getByTestId("reader-page")).toHaveValue("7");
    await reader.getByTestId("reader-scroll").evaluate((el) => { el.scrollTop += 120; });
    await expect.poll(() => reader.getByTestId("reader-page-view").nth(6).locator("canvas").evaluate((c: HTMLCanvasElement) => c.width), { timeout: 15_000 }).toBeGreaterThan(0); // page 7 is drawn
    await expect.poll(() => reader.getByTestId("reader-page-view").nth(13).locator("canvas").evaluate((c: HTMLCanvasElement) => c.width)).toBe(0); // page 14 is not
    // zoom keeps the reading place; fit-width resets
    const before = await reader.getByTestId("reader-page").inputValue();
    await reader.getByTestId("reader-zoom-in").click();
    await expect(reader.getByTestId("reader-zoom")).toHaveText("125%");
    await expect(reader.getByTestId("reader-page")).toHaveValue(before);
    await reader.getByTestId("reader-zoom").click();
    await expect(reader.getByTestId("reader-zoom")).toHaveText("100%");
    await page.waitForTimeout(1500); // saved (debounced)
    const saved = (await call("GET", `/medien/progress/BOOK/${free.id}`, tokenB)).json as { position: number; scroll: number | null; opened_at: string | null };
    expect(saved.position).toBe(Number(before));
    expect(saved.scroll).not.toBeNull();
    expect(saved.opened_at).not.toBeNull();
    await reader.getByTestId("reader-close").click();
    // reopen: the same page, continuous mode remembered; the button says so
    await page.reload();
    await expect(page.getByTestId("book-read")).toContainText(`${saved.position}`);
    await page.getByTestId("book-read").click();
    await expect(page.getByTestId("pdf-reader")).toHaveAttribute("data-mode", "scroll");
    await expect(page.getByTestId("reader-page")).toHaveValue(String(saved.position), { timeout: 30_000 });
    // book mode: previous / next, fullscreen toggle, the page is remembered too
    await page.getByTestId("reader-mode").click();
    await expect(page.getByTestId("pdf-reader")).toHaveAttribute("data-mode", "book");
    await expect(page.getByTestId("reader-page-view")).toHaveCount(1);
    await page.getByTestId("reader-next").click();
    await expect(page.getByTestId("reader-page")).toHaveValue(String(saved.position + 1));
    await page.getByTestId("reader-fullscreen").click();
    await expect(page.getByTestId("pdf-reader")).toBeVisible();
    await page.getByTestId("reader-fullscreen").click();
    await page.waitForTimeout(1500);
    await page.getByTestId("reader-close").click();
    expect(((await call("GET", `/medien/progress/BOOK/${free.id}`, tokenB)).json as { position: number }).position).toBe(saved.position + 1);
    // the continue list shows the book
    const cont = (await call("GET", "/medien/continue", tokenB)).json as { items?: { id: string }[] } | { id: string }[];
    const ids = (Array.isArray(cont) ? cont : (cont.items ?? [])).map((c) => c.id);
    expect(ids).toContain(free.id);
    // an IDOR attempt: B's position is B's own
    expect(((await call("GET", `/medien/progress/BOOK/${free.id}`, tokenA)).json as { position?: number } | null)?.position ?? null).not.toBe(saved.position + 1);
  });
});

// ---------------------------------------------------------------------------------------------------------------------------------------------------
test.describe("Bibliothek on a phone: continuous scroll, fit width, resume, paywall", () => {
  test.skip(({ isMobile }) => !isMobile, "desktop is covered above");
  test("the reader scrolls page after page without sideways scrolling, remembers the place and stops at the free pages", async ({ page }) => {
    const adminToken = await token(ADMIN.email, ADMIN.password);
    const free = await makeBook(adminToken, `${TAG} MobileFree`, { pages: 15 });
    const paid = await makeBook(adminToken, `${TAG} MobilePaid`, { paid: true, pages: 15 });
    try {
      const student = await createStudent();
      const bearer = await token(student, PASSWORD);
      await studentLogin(page, student);
      await page.goto(`/medien/bibliothek/${free.id}`);
      await noHorizontalScroll(page);
      await page.getByTestId("book-read").click();
      const reader = page.getByTestId("pdf-reader");
      await expect(reader.getByTestId("reader-canvas").first()).toBeVisible({ timeout: 30_000 });
      await expect(reader).toHaveAttribute("data-mode", "book"); // the default (swipe / pinch: medien-reader-shelf.spec.ts); this test is about the scroll mode
      await reader.getByTestId("reader-mode").click();
      await expect(reader).toHaveAttribute("data-mode", "scroll");
      await expect(reader.getByTestId("reader-page-view")).toHaveCount(15);
      const width = page.viewportSize()!.width;
      const sizes = await reader.getByTestId("reader-scroll").evaluate((el) => ({ scrollW: el.scrollWidth, clientW: el.clientWidth, page: (el.querySelector("[data-page]") as HTMLElement).getBoundingClientRect().width, gap: (el.querySelectorAll("[data-page]")[1] as HTMLElement).getBoundingClientRect().top - (el.querySelectorAll("[data-page]")[0] as HTMLElement).getBoundingClientRect().bottom }));
      expect(sizes.scrollW).toBeLessThanOrEqual(sizes.clientW + 1); // fits the width: no horizontal scroll
      expect(sizes.page).toBeLessThanOrEqual(width);
      expect(sizes.page).toBeGreaterThan(width * 0.8);
      expect(sizes.gap).toBeGreaterThanOrEqual(8); // space between the pages
      await noHorizontalScroll(page);
      // touch-style scrolling through the pages: the page counter follows
      await reader.getByTestId("reader-scroll").evaluate((el) => { el.scrollTop = (el.querySelectorAll("[data-page]")[4] as HTMLElement).offsetTop; });
      await expect.poll(() => reader.getByTestId("reader-page").inputValue(), { timeout: 10_000 }).toMatch(/^[45]$/);
      await expect(reader.getByTestId("reader-loading")).toHaveCount(0);
      await reader.getByTestId("reader-scroll").evaluate((el) => { el.scrollTop = (el.querySelectorAll("[data-page]")[8] as HTMLElement).offsetTop + 60; });
      await expect.poll(() => reader.getByTestId("reader-page").inputValue(), { timeout: 10_000 }).toBe("9");
      const top = await reader.getByTestId("reader-scroll").evaluate((el) => el.scrollTop);
      // zoom in: wider than the screen inside the reader (panning), still no document-wide sideways scroll
      await reader.getByTestId("reader-zoom-in").click();
      await reader.getByTestId("reader-zoom-in").click();
      expect(await reader.getByTestId("reader-scroll").evaluate((el) => el.scrollWidth > el.clientWidth)).toBe(true);
      await noHorizontalScroll(page);
      await reader.getByTestId("reader-zoom").click(); // back to fit-width
      expect(await reader.getByTestId("reader-scroll").evaluate((el) => el.scrollWidth <= el.clientWidth + 1)).toBe(true);
      await page.waitForTimeout(1500);
      await reader.getByTestId("reader-close").click();
      const saved = (await call("GET", `/medien/progress/BOOK/${free.id}`, bearer)).json as { position: number; scroll: number };
      expect(saved.position).toBe(9);
      expect(saved.scroll).toBeGreaterThanOrEqual(0);
      // continue reading: back on page 9 at about the same place
      await page.reload();
      await expect(page.getByTestId("book-read")).toContainText("9");
      await page.getByTestId("book-read").click();
      await expect(page.getByTestId("reader-page")).toHaveValue("9", { timeout: 30_000 });
      await expect.poll(() => page.getByTestId("reader-scroll").evaluate((el) => el.scrollTop), { timeout: 10_000 }).toBeGreaterThan(top - 140);
      expect(await page.getByTestId("reader-scroll").evaluate((el) => el.scrollTop)).toBeLessThan(top + 140);
      await page.getByTestId("reader-close").click();

      // paid book: ten free pages, then the purchase window — never page 11
      await page.goto(`/medien/bibliothek/${paid.id}`);
      await page.getByTestId("book-preview").click();
      const preview = page.getByTestId("pdf-reader");
      await expect(preview.getByTestId("reader-canvas").first()).toBeVisible({ timeout: 30_000 });
      await expect(preview.getByTestId("reader-page-view")).toHaveCount(10);
      await expect(preview.getByTestId("reader-locked-page")).toBeAttached();
      await preview.getByTestId("reader-scroll").evaluate((el) => { el.scrollTop = el.scrollHeight; });
      const paywall = preview.getByTestId("reader-paywall");
      await expect(paywall).toBeVisible();
      await expect(paywall).toContainText("Ushbu kitobning dastlabki 10 sahifasini bepul o‘qishingiz mumkin.");
      const box = await paywall.locator("[role=alertdialog]").boundingBox();
      expect(box!.width).toBeLessThanOrEqual(width);
      await expect(paywall.getByTestId("paywall-buy")).toBeVisible();
      await expect(paywall.getByTestId("paywall-back")).toBeVisible();
      await paywall.getByTestId("paywall-back").click();
      await expect(paywall).toHaveCount(0);
      await page.getByTestId("reader-close").click();
      // the payment window fits the phone
      await page.getByTestId("book-buy").click();
      const modal = page.getByTestId("book-payment-modal");
      await expect(modal.getByTestId("pay-card")).toBeVisible();
      const modalBox = await modal.locator("[role=dialog]").boundingBox();
      expect(modalBox!.width).toBeLessThanOrEqual(width + 1);
      await noHorizontalScroll(page);
      await modal.getByTestId("pay-submit").scrollIntoViewIfNeeded();
      await expect(modal.getByTestId("pay-submit")).toBeVisible();
    } finally {
      await call("DELETE", `/admin/medien/books/${free.id}`, adminToken);
      await call("DELETE", `/admin/medien/books/${paid.id}`, adminToken);
    }
  });
});
