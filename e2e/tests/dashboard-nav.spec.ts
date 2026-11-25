import { execFileSync } from "node:child_process";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

import { createStudent, loginViaForm, PASSWORD } from "./helpers";

// Student navigation redesign (2026-11-15): one "A1–C1 Kurse" entry + five hub cards, the language switcher on top of the sidebar
// (and of the mobile drawer), course overview with access statuses, old course URLs, certificates page. Local stack only;
// `psql` seeds one certificate for a test student in the local E2E database.

const PSQL = process.env.E2E_PSQL ?? "C:/Program Files/PostgreSQL/18/bin/psql.exe";
const DB = process.env.E2E_DB ?? "vizu_gcr_e2e";
const BACKEND = process.env.E2E_BACKEND_DIR ?? path.resolve(process.cwd(), "../backend");
const CERT_PDF = path.join(BACKEND, "uploads", "certificates", "e2e-nav-cert.pdf");

function sql(q: string) {
  return execFileSync(PSQL, ["-h", "127.0.0.1", "-p", "54329", "-U", "postgres", "-d", DB, "-tAc", q], { encoding: "utf8" }).trim();
}

const NAMES: Record<string, string[]> = {
  uz: ["A1–C1 Kurslar", "Medien", "Vorbereitung", "Sertifikatlar", "Xarid qilish"],
  de: ["A1–C1 Kurse", "Medien", "Vorbereitung", "Zertifikate", "Angebote"],
  en: ["A1–C1 Courses", "Media", "Preparation", "Certificates", "Purchase"],
  ru: ["A1–C1 Курсы", "Медиа", "Подготовка", "Сертификаты", "Покупка"],
};
const CARDS = ["courses", "media", "prep", "certificates", "purchase"];

/** Default language (German) — no init script, so a chosen language survives reloads like for a real user. */
async function login(page: Page) {
  const email = await createStudent();
  await loginViaForm(page, email, PASSWORD);
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 20_000 });
  return email;
}

async function expectHub(page: Page, lang: string) {
  for (const [i, id] of CARDS.entries()) {
    await expect(page.locator(`[data-testid="dashboard-hub"] [data-card="${id}"] h3`)).toHaveText(NAMES[lang][i]);
  }
}

const noOverflow = async (page: Page) => expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1);

test.describe("hub and course overview", () => {
  // the PWA service worker would answer fetches before page.route() sees them (status stub below)
  test.use({ serviceWorkers: "block" });
  test("five cards, each opens its page", async ({ page }) => {
    await login(page);
    for (const [id, url] of [["courses", /\/kurse$/], ["media", /\/medien$/], ["prep", /\/vorbereitung$/], ["certificates", /\/certificates$/], ["purchase", /\/angebote$/]] as const) {
      await page.goto("/dashboard");
      await page.locator(`[data-testid="dashboard-hub"] [data-card="${id}"]`).click();
      await expect(page).toHaveURL(url, { timeout: 15_000 });
      await expect(page.locator("main").first()).toBeVisible();
    }
    // quick buttons of the welcome header (2026-11-25)
    for (const [id, url] of [["my-teacher", /\/my-teacher$/], ["dictionary", /\/woerterbuch$/]] as const) {
      await page.goto("/dashboard");
      await page.locator(`[data-testid="quick-link"][data-link="${id}"]`).click();
      await expect(page).toHaveURL(url, { timeout: 15_000 });
      await expect(page.locator("main").first()).toBeVisible();
    }
  });

  test("/kurse: five level cards with their access status (real data)", async ({ page }) => {
    await login(page);
    await page.goto("/kurse");
    const cards = page.getByTestId("lms-level-card");
    await expect(cards).toHaveCount(5);
    expect(await cards.evaluateAll((els) => els.map((e) => e.getAttribute("data-level")))).toEqual(["A1", "A2", "B1", "B2", "C1"]);
    const label: Record<string, string> = { ACTIVE: "Aktiv", LOCKED: "Gesperrt", COMING_SOON: "Bald verfügbar", PURCHASE_REQUIRED: "Kauf erforderlich" };
    for (const c of await cards.all()) {
      const status = (await c.getAttribute("data-status"))!;
      expect(Object.keys(label)).toContain(status);
      await expect(c.getByTestId("lms-level-status")).toHaveText(label[status]);
      expect((await c.getAttribute("data-coming-soon")) === "true").toBe(status === "COMING_SOON");
    }
    await noOverflow(page);
  });

  test("/kurse: status mapping ACTIVE / PURCHASE_REQUIRED / LOCKED / COMING_SOON follows the backend data, texts per language", async ({ page }) => {
    await login(page);
    const sales: Record<string, Record<string, boolean>> = {
      A1: { owned: true, coming_soon: false, sales_enabled: true, sales_closed: false },
      A2: { owned: false, coming_soon: false, sales_enabled: true, sales_closed: false },
      B1: { owned: false, coming_soon: false, sales_enabled: true, sales_closed: true },
      B2: { owned: false, coming_soon: true, sales_enabled: false, sales_closed: false },
      C1: { owned: false, coming_soon: false, sales_enabled: false, sales_closed: false },
    };
    await page.route(/\/api\/v1\/lms\/levels(\?.*)?$/, async (route) => {
      const res = await route.fetch();
      const body = await res.json();
      for (const l of body.levels) l.sale = { ...l.sale, ...sales[l.level] };
      await route.fulfill({ response: res, json: body });
    });
    await page.goto("/kurse");
    const status = (level: string) => page.locator(`[data-testid="lms-level-card"][data-level="${level}"]`);
    const expected = { A1: "ACTIVE", A2: "PURCHASE_REQUIRED", B1: "LOCKED", B2: "COMING_SOON", C1: "LOCKED" };
    for (const [level, s] of Object.entries(expected)) await expect(status(level)).toHaveAttribute("data-status", s);
    const chip = (level: string) => status(level).getByTestId("lms-level-status");
    await expect(chip("A1")).toHaveText("Aktiv");
    await expect(chip("A2")).toHaveText("Kauf erforderlich");

    await page.evaluate(() => localStorage.setItem("vizu-language", JSON.stringify({ state: { language: "uz" }, version: 0 })));
    await page.reload();
    await expect(chip("A1")).toHaveText("Faol");
    await expect(chip("A2")).toHaveText("Xarid kerak");
    await expect(chip("B1")).toHaveText("Yopiq");
    await expect(chip("B2")).toHaveText("Tez orada");
    await expect(status("A1")).toContainText("Nemis tilida birinchi qadamlar");
    await page.evaluate(() => localStorage.setItem("vizu-language", JSON.stringify({ state: { language: "en" }, version: 0 })));
    await page.reload();
    await expect(chip("A1")).toHaveText("Active");
    await expect(chip("A2")).toHaveText("Purchase required");
    await expect(chip("B2")).toHaveText("Coming soon");
    await expect(status("A1")).toContainText("First steps in German");
  });

  test("old course URLs keep working", async ({ page }) => {
    await login(page);
    for (const level of ["a1", "a2", "b1", "b2", "c1"]) {
      const res = await page.goto(`/kurse/${level}`);
      expect(res!.status(), `/kurse/${level}`).toBeLessThan(400);
      await expect(page).toHaveURL(new RegExp(`/kurse/${level}$`));
      await expect(page.locator("main").first()).toBeVisible();
    }
    await page.goto("/courses");
    await expect(page).toHaveURL(/\/kurse$/);
    await page.goto("/courses/a2");
    await expect(page).toHaveURL(/\/kurse\/a2$/);
    await page.goto("/lessons");
    await expect(page).toHaveURL(/\/kurse$/);
  });
});

test.describe("language switcher — desktop sidebar", () => {
  test.beforeEach(({}, info) => test.skip(info.project.name === "mobile", "desktop sidebar"));

  test("on top of the sidebar (above the logo), the only level entry is one A1–C1 link", async ({ page }) => {
    await login(page);
    const aside = page.locator("aside");
    const box = aside.getByTestId("sidebar-language");
    await expect(box).toBeVisible();
    await expect(box.locator("button[data-lang]")).toHaveCount(4);
    expect(await box.locator("button[data-lang]").evaluateAll((els) => els.map((e) => e.getAttribute("data-lang")))).toEqual(["uz", "de", "en", "ru"]);
    // first element of the sidebar card, above the logo block and the navigation
    expect(await box.evaluate((el) => el.parentElement!.firstElementChild === el)).toBe(true);
    const lb = (await box.boundingBox())!;
    const logo = (await box.evaluate((el) => (el.nextElementSibling as HTMLElement).getBoundingClientRect().top))!;
    const navTop = (await aside.locator("nav").boundingBox())!.y;
    expect(lb.y + lb.height).toBeLessThanOrEqual(logo + 1);
    expect(logo).toBeLessThan(navTop);
    // one entry for all levels, no A1/A2/B1/B2/C1 entries
    await expect(aside.locator('a[href="/kurse"]')).toHaveCount(1);
    for (const level of ["a1", "a2", "b1", "b2", "c1"]) await expect(aside.locator(`a[href^="/kurse/${level}"]`)).toHaveCount(0);
    // the other sections are still there ("Hilfe Anfragen" became My Teacher in 2026-11-24; /support stays reachable through the help card)
    for (const href of ["/dashboard", "/vorbereitung", "/medien", "/angebote", "/certificates", "/settings", "/my-teacher", "/groups", "/woerterbuch", "/battle", "/informationen"]) {
      await expect(aside.locator(`a[href="${href}"]`)).toHaveCount(1);
    }
    // active language is marked
    await expect(box.locator('button[data-lang="de"]')).toHaveAttribute("aria-pressed", "true");
    await expect(box.locator('button[data-lang="uz"]')).toHaveAttribute("aria-pressed", "false");
    // the old switcher at the bottom is gone
    await expect(aside.locator("button[data-lang]")).toHaveCount(4);
  });

  test("UZ / DE / EN / RU translate the sidebar, hub and welcome; the choice survives a reload", async ({ page }) => {
    await login(page);
    const box = page.locator("aside").getByTestId("sidebar-language");
    await expectHub(page, "de");
    await expect(page.locator('aside a[href="/kurse"]')).toContainText("A1–C1 Kurse");
    const welcome: Record<string, string> = {};
    welcome.de = await page.getByTestId("dashboard-welcome").innerText();
    for (const lang of ["uz", "en", "ru", "de", "uz"]) {
      await box.locator(`button[data-lang="${lang}"]`).click();
      await expect(box.locator(`button[data-lang="${lang}"]`)).toHaveAttribute("aria-pressed", "true");
      await expectHub(page, lang);
      await expect(page.locator('aside a[href="/kurse"]')).toContainText(NAMES[lang][0]);
      await expect(page.locator('aside a[href="/angebote"]')).toContainText(NAMES[lang][4]);
      await expect(page.locator('aside a[href="/certificates"]')).toContainText(NAMES[lang][3]);
      if (lang === "uz") welcome.uz = await page.getByTestId("dashboard-welcome").innerText();
    }
    expect(welcome.uz).not.toEqual(welcome.de);
    // course names / descriptions on the overview follow the language
    await page.goto("/kurse");
    await expect(page.locator('[data-testid="lms-level-card"][data-level="A1"]')).toContainText("Nemis tilida birinchi qadamlar");
    // reload keeps UZ everywhere
    await page.goto("/dashboard");
    await page.reload();
    await expectHub(page, "uz");
    await expect(page.locator("aside").getByTestId("sidebar-language").locator('button[data-lang="uz"]')).toHaveAttribute("aria-pressed", "true");
    expect(await page.evaluate(() => JSON.parse(localStorage.getItem("vizu-language")!).state.language)).toBe("uz");
    await noOverflow(page);
  });

  test("collapsed sidebar: one button on top cycles the language", async ({ page }) => {
    await login(page);
    await page.getByRole("button", { name: "Sidebar einklappen" }).click();
    const compact = page.getByTestId("sidebar-language-compact");
    await expect(compact).toBeVisible();
    await expect(compact).toHaveAttribute("data-lang", "de");
    await compact.click(); // de → en
    await expect(compact).toHaveAttribute("data-lang", "en");
    await expectHub(page, "en");
    await compact.click(); // en → ru
    await expect(compact).toHaveAttribute("data-lang", "ru");
    await expectHub(page, "ru");
    await page.getByRole("button", { name: /Развернуть|Sidebar erweitern|Expand/ }).click();
    await expect(page.locator("aside").getByTestId("sidebar-language").locator('button[data-lang="ru"]')).toHaveAttribute("aria-pressed", "true");
  });
});

test.describe("language switcher — mobile drawer", () => {
  test.beforeEach(({}, info) => test.skip(info.project.name !== "mobile", "mobile drawer"));

  test("on top of the drawer, touch-friendly, switches and persists", async ({ page }) => {
    await login(page);
    await noOverflow(page);
    await page.getByRole("button", { name: "Menü öffnen" }).click();
    const box = page.getByTestId("mobile-language");
    await expect(box).toBeVisible();
    expect(await box.evaluate((el) => el.parentElement!.firstElementChild === el)).toBe(true);
    const buttons = box.locator("button[data-lang]");
    await expect(buttons).toHaveCount(4);
    for (const b of await buttons.all()) expect((await b.boundingBox())!.height).toBeGreaterThanOrEqual(44);
    expect((await box.boundingBox())!.y).toBeLessThan(((await page.getByRole("dialog").locator("nav").boundingBox())!).y);
    await expect(box.locator('button[data-lang="de"]')).toHaveAttribute("aria-pressed", "true");
    await box.locator('button[data-lang="uz"]').click();
    await expect(box.locator('button[data-lang="uz"]')).toHaveAttribute("aria-pressed", "true");
    await expect(page.getByRole("dialog").locator('a[href="/kurse"]')).toContainText("A1–C1 Kurslar");
    await expectHub(page, "uz");
    await page.reload();
    await expectHub(page, "uz");
    await page.getByRole("button", { name: /Menyuni ochish/ }).click();
    await expect(page.getByTestId("mobile-language").locator('button[data-lang="uz"]')).toHaveAttribute("aria-pressed", "true");
    // the drawer lists the single A1–C1 entry as well
    await expect(page.getByRole("dialog").locator('a[href^="/kurse"]')).toHaveCount(1);
  });
});

test.describe("certificates page", () => {
  test.afterAll(() => rmSync(CERT_PDF, { force: true }));

  test("empty state (Uzbek text)", async ({ page }) => {
    await login(page);
    await page.evaluate(() => localStorage.setItem("vizu-language", JSON.stringify({ state: { language: "uz" }, version: 0 })));
    await page.goto("/certificates");
    const empty = page.getByText("Hozircha sizda sertifikatlar mavjud emas.");
    await expect(empty).toBeVisible();
    await expect(page.getByText("O'qishni davom ettiring va yangi yutuqlarga erishing!")).toBeVisible();
    await expect(page.getByTestId("certificate-card")).toHaveCount(0);
    await noOverflow(page);
  });

  test("an issued certificate shows name, level, date, number and can be viewed, downloaded and printed; revoked ones are hidden", async ({ page }) => {
    const email = await login(page);
    const uid = sql(`SELECT id FROM users WHERE email = '${email}'`);
    mkdirSync(path.dirname(CERT_PDF), { recursive: true });
    writeFileSync(CERT_PDF, "%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\ntrailer<</Root 1 0 R/Size 4>>\n%%EOF\n");
    const stamp = Date.now();
    const insert = (n: number, level: string, valid: boolean) =>
      sql(`INSERT INTO certificates (id, user_id, source, certificate_number, verification_code, provider, level, lesen_score, hoeren_score, schreiben_score, sprechen_score, score, pdf_url, issued_at, is_valid)
           VALUES (gen_random_uuid(), '${uid}', 'COURSE', 'E2E-NAV-${stamp}-${n}', 'E2EV-${stamp}-${n}', 'VIZU', '${level}', 80, 80, 80, 80, 80, 'uploads/certificates/e2e-nav-cert.pdf', '2026-03-15 12:00:00', ${valid})`);
    insert(1, "A2", true);
    insert(2, "B1", false);

    await page.goto("/certificates");
    const cards = page.getByTestId("certificate-card");
    await expect(cards).toHaveCount(1); // the revoked B1 certificate is not shown
    const card = cards.first();
    await expect(card).toContainText("A2");
    await expect(card).toContainText(`E2E-NAV-${stamp}-1`);
    await expect(card).toContainText(/15\.3\.2026/);
    await expect(card).toContainText("Kursabschluss");
    await expect(page.getByText(`E2E-NAV-${stamp}-2`)).toHaveCount(0);
    await noOverflow(page);

    const pdfResponse = (btn: () => Promise<void>) => Promise.all([page.waitForResponse((r) => /\/my-certificates\/.+\/pdf/.test(r.url())), btn()]).then(([r]) => r);
    // view
    const view = await pdfResponse(() => card.locator("button", { has: page.locator("svg.lucide-eye") }).click());
    expect(view.status()).toBe(200);
    expect(view.headers()["content-type"]).toContain("application/pdf");
    // download
    const [download] = await Promise.all([page.waitForEvent("download"), card.getByTestId("certificate-pdf").click()]);
    expect(download.suggestedFilename()).toBe(`Zertifikat-E2E-NAV-${stamp}-1.pdf`);
    // print: fetches the PDF and hands it to a hidden iframe
    const print = await pdfResponse(() => card.getByTestId("certificate-print").click());
    expect(print.status()).toBe(200);
    await expect(page.locator('iframe[aria-hidden="true"]')).toHaveCount(1);
    expect(await page.locator('iframe[aria-hidden="true"]').getAttribute("src")).toMatch(/^blob:/);
  });
});