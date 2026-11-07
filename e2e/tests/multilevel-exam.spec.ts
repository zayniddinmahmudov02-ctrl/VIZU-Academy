import { expect, test, type Page } from "@playwright/test";

import { ADMIN, PASSWORD, createStudent, loginViaForm, useLanguage } from "./helpers";

// Multilevel exam mode (local stack; needs a PUBLISHED, complete "Modelltest 1" in "Multilevel B1–C1" — local seed
// D:\vz_tmp\work\ml_e2e_seed.py). Student: no level choice, timed section, answers saved and changeable, submit,
// finish, result x / 75 + total / 300. Admin: results page, grading Schreiben, preview, settings.

async function noHorizontalScroll(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(1);
}

async function confirmDialog(page: Page, label: string) {
  await page.locator("div.fixed").getByRole("button", { name: label }).click();
}

test.describe.serial("multilevel exam", () => {
  let studentEmail = "";

  test("student takes the exam without choosing a level", async ({ page }, info) => {
    await useLanguage(page, "de");
    studentEmail = await createStudent();
    await loginViaForm(page, studentEmail, PASSWORD);
    await expect(page).toHaveURL(/\/dashboard/);

    await page.goto("/vorbereitung/multilevel");
    await expect(page.getByRole("heading", { name: /Multilevel · B1–C1/ })).toBeVisible();
    await expect(page.getByText("Prüfung ohne Niveauwahl")).toBeVisible();
    const card = page.getByTestId("multilevel-exam-1");
    await expect(card).toBeVisible();
    await noHorizontalScroll(page);
    await card.getByTestId("start-exam").click();
    await expect(page.getByTestId("exam-overview")).toBeVisible();
    await page.screenshot({ path: `test-results/multilevel-overview-${info.project.name}.png`, fullPage: true });

    // Lesen: answer, change, reload → still saved
    await page.getByTestId("exam-section-LESEN").getByRole("button", { name: "Teil starten" }).click();
    await expect(page.getByTestId("exam-section")).toBeVisible();
    const first = page.getByTestId("exam-question").first();
    await first.getByTestId("exam-option").nth(0).click();
    await first.getByTestId("exam-option").nth(1).click();
    await expect(first.getByText("Gespeichert")).toBeVisible();
    await noHorizontalScroll(page);
    await page.screenshot({ path: `test-results/multilevel-lesen-${info.project.name}.png` });
    await page.reload();
    await page.getByTestId("exam-section-LESEN").getByRole("button", { name: "Weiter" }).click();
    await expect(page.getByTestId("exam-question").first().getByTestId("exam-option").nth(1)).toHaveAttribute("aria-pressed", "true");
    // no keys in the student paper
    expect(await page.content()).not.toContain("is_correct");
    await page.getByTestId("submit-section").click();
    await confirmDialog(page, "Teil abgeben");
    await expect(page.getByTestId("exam-section-LESEN").getByText("Abgegeben")).toBeVisible({ timeout: 10_000 });

    // Schreiben: text is saved
    await page.getByTestId("exam-section-SCHREIBEN").getByRole("button", { name: "Teil starten" }).click();
    const box = page.getByTestId("writing-answer").first();
    await box.fill("Liebe Anna, ich finde den Umzug der Sprachschule gut, weil die Räume moderner werden.");
    await expect(page.getByText("Gespeichert").first()).toBeVisible({ timeout: 10_000 });
    await page.getByTestId("submit-section").click();
    await confirmDialog(page, "Teil abgeben");
    await expect(page.getByTestId("exam-section-SCHREIBEN").getByText("Abgegeben")).toBeVisible({ timeout: 10_000 });

    // finish: Hören / Sprechen not started → 0
    await page.getByTestId("finish-exam").click();
    await confirmDialog(page, "Prüfung beenden");
    await expect(page).toHaveURL(/\/vorbereitung\/multilevel\/ergebnis\//);
    await expect(page.getByTestId("result-LESEN")).toContainText("/ 75");
    await expect(page.getByTestId("result-HOEREN")).toContainText("0");
    await expect(page.getByTestId("result-SCHREIBEN")).toContainText("Wird von der Lehrkraft bewertet");
    await expect(page.getByTestId("overall-level")).toHaveText("Ausstehend");
    await noHorizontalScroll(page);
    await page.screenshot({ path: `test-results/multilevel-result-${info.project.name}.png`, fullPage: true });

    // history + profile
    await page.goto("/vorbereitung/multilevel");
    await expect(page.getByTestId("multilevel-history")).toContainText("Modelltest 1");
    await expect(page.getByTestId("multilevel-exam-1").getByTestId("start-exam")).toHaveText(/Erneut ablegen/);
    await page.goto("/settings");
    await expect(page.getByTestId("profile-multilevel")).toContainText("Modelltest 1");
  });

  test("admin sees the attempt, grades Schreiben and previews the test", async ({ page, isMobile }) => {
    test.skip(isMobile, "admin checks run on desktop");
    await loginViaForm(page, ADMIN.email, ADMIN.password);
    await page.getByPlaceholder("Admin-Passwort").fill(ADMIN.verify);
    await page.getByRole("button", { name: "Bestätigen" }).click();
    await expect(page).toHaveURL(/\/admin/);
    await expect(page.getByRole("link", { name: "Stufe Bestimmung", exact: true })).toBeVisible();
    await page.getByRole("link", { name: "Multilevel (National Zertifikat)" }).click();
    await expect(page.getByRole("heading", { name: /Multilevel B1–C1 · National Zertifikat/ })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Bewertungsregeln" })).toBeVisible();
    await expect(page.getByTestId("setting-overall")).toHaveValue("UNCONFIRMED");
    await expect(page.getByTestId("setting-score-50")).toHaveValue("UNGEKLAERT");

    const row = page.locator("tr", { hasText: "Modelltest 1" }).first();
    await expect(row).toBeVisible();
    await row.click();
    const grade = page.getByTestId("grade-SCHREIBEN");
    await grade.getByRole("spinbutton").fill("60");
    await grade.getByRole("button", { name: "Bewerten" }).click();
    await expect(grade.getByText("Gespeichert.")).toBeVisible();
    await page.screenshot({ path: "test-results/multilevel-admin.png", fullPage: true });

    await page.locator("a[title='Vorschau']").first().click();
    await expect(page.getByRole("heading", { name: /Vorschau · Modelltest 1/ })).toBeVisible();
    await expect(page.getByTestId("paper-teil").first()).toBeVisible();
  });
});
