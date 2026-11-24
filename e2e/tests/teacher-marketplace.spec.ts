import { execFileSync } from "node:child_process";

import { expect, test, type Locator, type Page } from "@playwright/test";

import { ADMIN, loginViaForm, useLanguage } from "./helpers";

/** My Teacher / Teacher Marketplace end to end on the local stack (never production): teacher profile with a 9:16 photo,
 * own courses + approval, free and paid enrollment (manual card transfer approved in Admin → Payments), a real review,
 * admin moderation, and a free special lesson in a REAL local LiveKit room (muted students, camera permission, server
 * countdown, automatic close by the backend scheduler). Seed before each run: D:\vz_tmp\work\tm_e2e_seed.py.
 * The live part moves the lesson start with a local helper (E2E_PYTHON + E2E_TM_SHIFT), because the API never allows a
 * start under one hour ahead; the backend must run with the scheduler on (APP_ENV other than "test"). */

const PASSWORD = "Geheim123!";
const TEACHER = "tm-teacher@example.com";
const STUDENT = "tm-student1@example.com";
const RUN = Date.now().toString(36).slice(-5);
const PAID = `E2E Pullik kurs ${RUN}`;
const FREE = `E2E Bepul kurs ${RUN}`;
const LESSON = `E2E Maxsus dars ${RUN}`;
const FAKE_MEDIA = ["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "--autoplay-policy=no-user-gesture-required"];

test.use({ launchOptions: { args: FAKE_MEDIA }, permissions: ["camera", "microphone"] });
test.describe.configure({ mode: "serial" });

/** today / a time ten minutes ago in Tashkent (the backend's calendar) */
function tashkent(offsetMinutes = 0) {
  const d = new Date(Date.now() + offsetMinutes * 60_000);
  const parts = Object.fromEntries(new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Tashkent", year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(d).map((p) => [p.type, p.value]));
  return { date: `${parts.year}-${parts.month}-${parts.day}`, time: `${parts.hour}:${parts.minute}` };
}

async function login(page: Page, email: string) {
  await loginViaForm(page, email, PASSWORD);
  await page.waitForURL((u) => !u.pathname.startsWith("/login"), { timeout: 20_000 });
  await useLanguage(page, "uz");
}

async function adminLogin(page: Page) {
  await loginViaForm(page, ADMIN.email, ADMIN.password);
  await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
  await page.getByRole("button", { name: "Bestätigen" }).click();
  await expect(page).toHaveURL(/\/admin/);
}

async function noHorizontalScroll(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
}

/** A picture drawn in the browser (no fixture file): gradient + text, given size. */
async function picture(page: Page, w: number, h: number): Promise<Buffer> {
  const b64 = await page.evaluate(([width, height]) => {
    const c = document.createElement("canvas");
    c.width = width;
    c.height = height;
    const g = c.getContext("2d")!;
    const grad = g.createLinearGradient(0, 0, width, height);
    grad.addColorStop(0, "#1d4ed8");
    grad.addColorStop(1, "#f59e0b");
    g.fillStyle = grad;
    g.fillRect(0, 0, width, height);
    g.fillStyle = "#fff";
    g.font = "bold 120px sans-serif";
    g.fillText("VIZU", 60, height / 2);
    return c.toDataURL("image/png").split(",")[1];
  }, [w, h]);
  return Buffer.from(b64, "base64");
}

async function ratioOf(locator: Locator): Promise<number> {
  const box = await locator.boundingBox();
  expect(box).toBeTruthy();
  return box!.height / box!.width;
}

const row = (page: Page, testId: string, text: string) => page.getByTestId(testId).filter({ hasText: text });

/** A control of the meeting's bottom bar; on narrow screens the secondary ones sit in "More". */
async function control(page: Page, testId: string): Promise<Locator> {
  const visible = page.getByTestId(testId).locator("visible=true");
  if (await visible.count()) return visible.first();
  await page.getByTestId("ctl-more").click();
  return page.getByTestId(testId).locator("visible=true").first();
}

test.describe("teacher marketplace", () => {
  test.beforeEach(({}, info) => test.skip(info.project.name !== "desktop", "the flow runs once on desktop; phone layout has its own test"));

  test("teacher: public profile with a 9:16 photo, read-only rating, two courses submitted, a special lesson requested", async ({ page }) => {
    test.setTimeout(120_000);
    await login(page, TEACHER);
    await page.goto("/teacher/profil");
    await expect(page.getByTestId("teacher-profile-editor")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByTestId("profile-state")).toBeVisible();

    await page.getByTestId("pf-headline").fill("Goethe-Zertifikat imtihonlariga tayyorlov");
    await page.getByTestId("pf-bio").fill("Nemis tilini 8 yildan beri o'rgataman.");
    await page.getByTestId("pf-years").fill("8");
    await page.getByTestId("pf-since").fill("2017");
    await page.getByTestId("pf-spec").fill("Grammatik, Sprechen");
    for (const l of ["Deutsch", "Usbekisch"]) await page.getByTestId("pf-languages").getByRole("button", { name: l, exact: true }).click();
    for (const l of ["A1", "A2", "B1"]) await page.getByTestId("pf-levels").getByRole("button", { name: l, exact: true }).click();
    await page.getByTestId("pf-save").click();
    await expect(page.getByTestId("pf-saved")).toBeVisible();

    // 9:16 photo: pick, crop box, save → re-encoded 720 × 1280 WebP
    await page.getByTestId("photo-cropper-input").setInputFiles({ name: "foto.png", mimeType: "image/png", buffer: await picture(page, 1000, 1500) });
    await expect(page.getByTestId("crop-box")).toBeVisible();
    await page.getByTestId("photo-cropper-save").click();
    const photo = page.getByTestId("photo-panel").locator("img").first();
    await expect(photo).toHaveAttribute("src", /teacher-market\/photos\/.+\.webp/, { timeout: 15_000 });
    await expect.poll(() => photo.evaluate((i: HTMLImageElement) => `${i.naturalWidth}x${i.naturalHeight}`)).toBe("720x1280");
    expect(await ratioOf(photo)).toBeCloseTo(16 / 9, 1);

    // the rating is shown, never editable by the teacher
    await expect(page.getByTestId("own-rating")).toContainText("—");
    await expect(page.getByTestId("own-rating").locator("[data-testid^='star-']")).toHaveCount(0);

    await page.getByTestId("profile-preview-toggle").click();
    await expect(page.getByTestId("profile-name")).toHaveText("Malika Karimova");
    await page.getByTestId("profile-preview-toggle").click();

    // two courses: paid (250 000 so'm) and free, both start today with open enrollment
    await page.goto("/teacher/meine-kurse");
    const today = tashkent().date;
    for (const [title, type] of [[PAID, "PAID"], [FREE, "FREE"]] as const) {
      await page.getByTestId("course-new").click();
      const form = page.getByTestId("course-form");
      await form.getByTestId("cf-title").fill(title);
      await form.getByTestId("cf-description").fill("Har hafta 3 dars, uy vazifalari bilan.");
      await form.getByTestId("cf-type").selectOption(type);
      await form.getByTestId("cf-level").selectOption("A2");
      if (type === "PAID") await form.getByTestId("cf-price").fill("250000");
      await form.getByTestId("cf-max").fill("10");
      await form.getByTestId("cf-status").selectOption("ANMELDUNG");
      await form.getByTestId("cf-start").fill(today);
      await form.getByTestId("cf-save").click();
      await expect(page.getByTestId("course-image")).toBeVisible(); // the saved course stays open for the image
      await page.getByTestId("course-editor").getByTestId("modal-close").click();
      const own = row(page, "own-course", title);
      await expect(own.getByTestId("own-course-approval")).toBeVisible();
      await own.getByTestId("own-course-submit").click();
      await expect(own.getByTestId("own-course-submit")).toHaveCount(0);
    }

    // free special lesson request (the default start is tomorrow)
    await page.goto("/teacher/spezialstunden");
    await page.getByTestId("lesson-new").click();
    await page.getByTestId("lf-title").fill(LESSON);
    await page.getByTestId("lf-topic").fill("Perfekt");
    await page.getByTestId("lf-level").selectOption("A2");
    await page.getByTestId("lf-duration").fill("15");
    await page.getByTestId("lf-max").fill("20");
    await page.getByTestId("lf-submit").click();
    await expect(row(page, "own-lesson", LESSON).getByTestId("own-lesson-status")).toBeVisible();
    await expect(row(page, "own-lesson", LESSON).getByTestId("lesson-open")).toHaveCount(0);
  });

  test("admin: verifies the teacher, approves both courses and the special lesson", async ({ page }) => {
    test.setTimeout(90_000);
    page.on("dialog", (d) => void d.accept());
    await adminLogin(page);
    await page.goto("/admin/lehrer-marktplatz");
    await expect(page.getByTestId("market-overview")).toBeVisible({ timeout: 20_000 });

    await page.getByTestId("market-tab-lehrer").click();
    await page.getByTestId("admin-teacher-search").fill("Malika");
    const teacher = page.getByTestId("admin-teacher-row").filter({ hasText: "Malika Karimova" });
    await expect(teacher).toHaveCount(1);
    await teacher.getByTestId("admin-teacher-verified").click();
    await expect(teacher.getByTestId("admin-teacher-verified")).toHaveAttribute("data-checked", "");

    await page.getByTestId("market-tab-kurse").click();
    for (const title of [PAID, FREE]) {
      const course = row(page, "admin-course-row", title);
      await course.getByTestId("admin-course-approve").click();
      await expect(course).toHaveCount(0); // gone from "Zur Freigabe"
    }
    await page.getByTestId("admin-course-filter").selectOption("APPROVED");
    await expect(row(page, "admin-course-row", PAID)).toContainText("250 000");

    await page.getByTestId("market-tab-spezialstunden").click();
    const lesson = row(page, "admin-lesson-row", LESSON);
    await lesson.getByTestId("admin-lesson-approve").click();
    await expect(lesson).toHaveCount(0);
  });

  test("student: catalog, profile, free and paid enrollment (payment approved by the admin), a real review", async ({ page, browser }) => {
    test.setTimeout(150_000);
    await login(page, STUDENT);
    await page.goto("/dashboard");
    // "Hilfe Anfragen" is replaced by My Teacher in the menu; the old support page still works
    await expect(page.locator('aside nav a[href="/my-teacher"]')).toBeVisible({ timeout: 20_000 });
    await expect(page.locator('aside nav a[href="/support"]')).toHaveCount(0);
    expect((await page.goto("/support"))?.status()).toBeLessThan(400);

    await page.goto("/my-teacher");
    await expect(page.getByTestId("my-teacher-catalog")).toBeVisible({ timeout: 20_000 });
    await page.getByTestId("catalog-search").fill("Malika");
    const card = page.getByTestId("teacher-card").filter({ hasText: "Malika Karimova" });
    await expect(card).toHaveCount(1, { timeout: 15_000 });
    await expect(page.getByTestId("teacher-card")).toHaveCount(1);
    expect(await ratioOf(card.locator("img").first())).toBeCloseTo(16 / 9, 1); // 9:16 portrait, photo + name only
    await page.getByTestId("catalog-search").fill("Bekzod");
    await expect(page.getByTestId("teacher-card").filter({ hasText: "Bekzod Aliyev" }).getByTestId("teacher-photo-placeholder")).toBeVisible();
    await page.getByTestId("catalog-search").fill("Malika");
    await card.click();

    await expect(page.getByTestId("profile-name")).toHaveText("Malika Karimova");
    await expect(page.getByTestId("verified-badge")).toBeVisible();
    await expect(page.getByTestId("profile-rating")).not.toContainText("/5");
    await expect(page.getByTestId("stat-current")).toHaveText("0");

    // free course: enrolled at once
    await row(page, "course-card", FREE).getByTestId("course-open").click();
    const dialog = page.getByTestId("course-dialog");
    await dialog.getByTestId("enroll-free").click();
    await expect(dialog.getByTestId("my-enrollment")).toBeVisible();
    await expect(dialog.getByTestId("to-classroom")).toBeVisible();
    await dialog.getByTestId("modal-close").click();

    // paid course: card transfer without a receipt → pending, no access yet
    await row(page, "course-card", PAID).getByTestId("course-open").click();
    await dialog.getByTestId("enroll-paid").click();
    await expect(dialog.getByTestId("payment-amount")).toContainText("250 000");
    const paidAt = tashkent(-10);
    await dialog.getByTestId("payment-no-receipt").check();
    await dialog.getByTestId("payment-date").fill(paidAt.date);
    await dialog.getByTestId("payment-time").fill(paidAt.time);
    await dialog.getByTestId("payment-submit").click();
    await expect(dialog.getByTestId("course-message")).toBeVisible();
    await expect(dialog.getByTestId("my-enrollment")).toBeVisible(); // waiting for payment: the seat is held, no classroom yet
    await expect(dialog.getByTestId("to-classroom")).toHaveCount(0);
    await dialog.getByTestId("modal-close").click();

    // the Super Admin approves it in Admin → Payments → Payment Requests
    const actx = await browser.newContext();
    const admin = await actx.newPage();
    admin.on("dialog", (d) => void d.accept());
    await adminLogin(admin);
    await admin.goto("/admin/payments");
    await admin.getByRole("tab", { name: "Payment Requests", exact: true }).click();
    const buyer = admin.locator('[data-testid="buyer-card"][data-category="TEACHER_COURSES"]').filter({ hasText: "Sardor" });
    await expect(buyer).toHaveCount(1, { timeout: 15_000 });
    await expect(buyer).toContainText(`My Teacher Kurs: ${PAID}`);
    await buyer.getByRole("button", { name: "Genehmigen" }).click();
    await expect(buyer).toHaveCount(0, { timeout: 15_000 });
    await actx.close();

    await page.goto("/my-teacher/meine-kurse");
    for (const title of [PAID, FREE]) await expect(row(page, "my-course-row", title).getByTestId("my-course-status")).toBeVisible();
    await expect(page.getByTestId("my-course-row")).toHaveCount(2);

    // a real review (the course started today and the enrollment is active)
    await page.goBack();
    await page.reload();
    await expect(page.getByTestId("stat-current")).toHaveText("1");
    await expect(page.getByTestId("stat-total")).toHaveText("1"); // one student, two courses: counted once
    await page.getByTestId("review-form").getByTestId("star-5").click();
    await page.getByTestId("review-body").fill("Juda tushunarli tushuntiradi, darslar qiziqarli.");
    await page.getByTestId("review-save").click();
    await expect(page.getByTestId("review-saved")).toBeVisible();
    await expect(page.getByTestId("profile-rating")).toContainText("5.0/5");
    const review = page.getByTestId("review-item").first();
    await expect(review.getByTestId("review-author")).toHaveText(/^Sardor R\.?/); // short name, no e-mail
    await expect(review).not.toContainText("@");
  });

  test("teacher: sees the rating read-only, reports the review, the roster shows the payment; admin dismisses the report", async ({ page, browser }) => {
    test.setTimeout(90_000);
    await login(page, TEACHER);
    await page.goto("/teacher/bewertungen");
    await expect(page.getByTestId("own-rating-value")).toHaveText("5.0/5", { timeout: 20_000 });
    await expect(page.getByTestId("teacher-reviews").locator("textarea, [data-testid^='star-']")).toHaveCount(0);
    await page.getByTestId("teacher-review").first().getByTestId("teacher-review-report").click();
    await page.getByRole("dialog").locator("textarea").fill("Test: noto'g'ri kurs ko'rsatilgan");
    await page.getByRole("dialog").getByRole("button").last().click();
    await expect(page.getByTestId("teacher-review-report")).toHaveCount(0);

    await page.goto("/teacher/meine-kurse");
    await row(page, "own-course", PAID).getByTestId("own-course-roster").click();
    await expect(page.getByTestId("roster-dialog").getByTestId("roster-row").filter({ hasText: "Sardor" })).toHaveCount(1);

    const actx = await browser.newContext();
    const admin = await actx.newPage();
    await adminLogin(admin);
    await admin.goto("/admin/lehrer-marktplatz?tab=bewertungen");
    const reported = admin.getByTestId("admin-review-row").filter({ hasText: PAID });
    await expect(reported).toContainText("Meldung");
    await reported.getByRole("button", { name: "Meldungen schließen" }).click();
    await expect(reported).toHaveCount(0, { timeout: 15_000 });
    await actx.close();
  });

  test("special lesson: Global Chat shows it, muted students, camera permission, server countdown, automatic close", async ({ page, browser }) => {
    const python = process.env.E2E_PYTHON;
    const shift = process.env.E2E_TM_SHIFT;
    test.skip(!python || !shift, "needs E2E_PYTHON + E2E_TM_SHIFT (local helper that moves the lesson start into the open window)");
    test.setTimeout(420_000);
    // start 12 minutes ago, 15 minutes long: the backend closes the room in about 3 minutes
    execFileSync(python!, [shift!, LESSON, "-12"], { stdio: "pipe" });
    page.on("dialog", (d) => void d.accept());

    await login(page, TEACHER);
    await page.goto("/teacher/spezialstunden");
    await row(page, "own-lesson", LESSON).getByTestId("lesson-open").click();
    await page.waitForURL(/\/video-room\//, { timeout: 20_000 });
    await expect(page.getByTestId("prejoin-ends-at")).toBeVisible({ timeout: 20_000 });
    await page.getByTestId("video-join").click();
    await expect(page.getByTestId("meeting")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByTestId("meeting-time-left")).toHaveAttribute("data-soon", "1");
    await expect(page.getByTestId("meeting-toast").filter({ hasText: "5 daqiqa" })).toBeVisible({ timeout: 10_000 });

    // the student finds it in the Global Chat (announcement + Join) and on the live page
    const sctx = await browser.newContext({ permissions: ["camera", "microphone"] });
    const s = await sctx.newPage();
    await login(s, STUDENT);
    await s.goto("/dashboard");
    await s.getByTestId("global-chat-button").click();
    await expect(s.getByTestId("chat-live-lessons")).toContainText(LESSON, { timeout: 20_000 });
    await expect(s.getByTestId("global-chat-list")).toContainText(LESSON); // the announcement the approval posted
    await s.getByTestId("chat-live-lessons").getByTestId("lesson-join").click();
    await s.waitForURL(/\/video-room\//);
    await expect(s.getByTestId("prejoin")).toBeVisible({ timeout: 20_000 });
    await expect(s.getByTestId("prejoin-cam-locked")).toBeVisible(); // participants join without camera …
    await expect(s.getByTestId("prejoin-mic")).toBeDisabled(); // … and muted
    await s.getByTestId("video-join").click();
    await expect(s.getByTestId("meeting")).toBeVisible({ timeout: 20_000 });
    await expect(s.getByTestId("ctl-mic")).toBeDisabled();
    await expect(s.getByTestId("ctl-camera")).toBeDisabled();
    await expect(s.getByTestId("meeting-time-left")).toBeVisible();

    // the teacher allows this student's camera; the student turns it on and the teacher sees the video
    await (await control(page, "ctl-participants")).click();
    const studentRow = page.getByTestId("participant-row").filter({ hasText: "Sardor" });
    await expect(studentRow).toHaveCount(1, { timeout: 15_000 });
    const identity = (await studentRow.getAttribute("data-identity")) ?? "";
    await studentRow.getByTestId("participant-actions").click();
    await page.getByTestId("action-camera").click();
    await expect(s.getByTestId("meeting-toast").filter({ hasText: "kamerangizni" })).toBeVisible({ timeout: 15_000 });
    await expect(s.getByTestId("ctl-camera")).toBeEnabled();
    await s.getByTestId("ctl-camera").click();
    await expect.poll(() => page.locator(`[data-testid="video-tile"][data-identity="${identity}"][data-source="camera"] video`)
      .evaluate((v: HTMLVideoElement) => v.videoWidth).catch(() => 0), { timeout: 25_000 }).toBeGreaterThan(0);

    // nobody ends it: the backend closes the room at the hard end and LiveKit disconnects both
    for (const p of [page, s]) await expect(p.getByTestId("video-over")).toHaveAttribute("data-reason", "ended", { timeout: 300_000 });
    await page.goto("/teacher/spezialstunden");
    await expect(row(page, "own-lesson", LESSON).getByTestId("own-lesson-status")).not.toHaveText(/tasdiq|genehmigt/i);
    await s.goto("/my-teacher/live");
    await expect(s.getByTestId("lessons-past")).toContainText(LESSON, { timeout: 20_000 });
    await sctx.close();
  });
});

test("phone: catalog and profile fit the screen", async ({ page }, info) => {
  test.skip(info.project.name !== "mobile", "phone layout only");
  await login(page, STUDENT);
  await page.goto("/my-teacher");
  await expect(page.getByTestId("teacher-grid")).toBeVisible({ timeout: 20_000 });
  await noHorizontalScroll(page);
  const first = page.getByTestId("teacher-card").first();
  const box = await first.boundingBox();
  expect(box!.width).toBeLessThan(page.viewportSize()!.width / 2 + 1); // at least two portrait cards per row
  await first.click();
  await expect(page.getByTestId("teacher-profile")).toBeVisible();
  await noHorizontalScroll(page);
  await page.goto("/my-teacher/live");
  await expect(page.getByTestId("my-teacher-live")).toBeVisible();
  await noHorizontalScroll(page);
});
