import { expect, test, type Locator, type Page } from "@playwright/test";

import { API_URL, loginViaForm, useLanguage } from "./helpers";

// Global Chat replies against the throwaway stack (README.md). Same users as
// global-chat.spec.ts (gc-student1 "Sami", gc-student2 "Lola", password Geheim123!).
const STUDENT1 = "gc-student1@example.com";
const STUDENT2 = "gc-student2@example.com";
const PASSWORD = "Geheim123!";

async function apiToken(identifier: string): Promise<string> {
  const res = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ identifier, password: PASSWORD }),
  });
  expect(res.status, await res.clone().text()).toBe(200);
  return (await res.json()).access_token;
}

async function apiPost(token: string, body: string, replyToId?: string) {
  await new Promise((r) => setTimeout(r, 1100)); // the server allows one message per second and sender
  return fetch(`${API_URL}/api/v1/global-chat/messages`, {
    method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(replyToId ? { body, reply_to_id: replyToId } : { body }),
  });
}

/** The message itself — not a reply that quotes its text. */
function messageWith(page: Page, text: string): Locator {
  return page.locator("[data-testid=global-chat-message]:not(:has([data-testid=global-chat-reply-quote]))").filter({ hasText: text });
}

async function openChat(page: Page) {
  await useLanguage(page, "de");
  await loginViaForm(page, STUDENT1, PASSWORD);
  await expect(page).toHaveURL(/\/dashboard/);
  await page.getByTestId("global-chat-button").click();
  await expect(page.getByTestId("global-chat-panel")).toBeVisible();
}

/** A touch swipe as the browser sends it (pointer events with pointerType "touch"). */
async function swipe(target: Locator, dx: number, dy: number) {
  const box = (await target.boundingBox())!;
  const x = box.x + box.width / 2;
  const y = box.y + box.height / 2;
  const base = { pointerType: "touch", pointerId: 7, isPrimary: true, bubbles: true, button: 0 };
  await target.dispatchEvent("pointerdown", { ...base, clientX: x, clientY: y, buttons: 1 });
  for (let i = 1; i <= 6; i++) {
    await target.dispatchEvent("pointermove", { ...base, clientX: x + (dx * i) / 6, clientY: y + (dy * i) / 6, buttons: 1 });
  }
  await target.dispatchEvent("pointerup", { ...base, clientX: x + dx, clientY: y + dy, buttons: 0 });
}

test.describe("Global Chat replies", () => {
  test("API: a reply needs a real Global Chat message, the quote comes from the server", async () => {
    const token = await apiToken(STUDENT2);
    const bad = await apiPost(token, "Antwort ins Leere", "00000000-0000-0000-0000-000000000000");
    expect(bad.status).toBe(422);
    expect(JSON.stringify(await bad.json())).toContain("reply_not_found");
    const forged = await fetch(`${API_URL}/api/v1/global-chat/messages`, {
      method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ body: "x", reply_to_id: "00000000-0000-0000-0000-000000000000", reply_to_body: "gefälscht" }),
    });
    expect(forged.status).toBe(422); // unknown fields are refused
    const original = await (await apiPost(token, `Original ${Date.now()}`)).json();
    const reply = await (await apiPost(token, `meine Antwort 👍 ${Date.now()}`, original.id)).json();
    expect(reply.reply_to).toMatchObject({ id: original.id, available: true, sender: { name: "Lola Lernende" } });
  });

  test("reply with the button: preview, cancel, send, jump to the original", async ({ page }) => {
    const other = await apiToken(STUDENT2);
    const text = `Wer kommt morgen? ${Date.now()}`;
    expect((await apiPost(other, text)).status).toBe(201);
    await openChat(page);
    const original = messageWith(page, text);
    await expect(original).toBeVisible();

    await original.hover();
    await original.getByTestId("global-chat-reply").click();
    const preview = page.getByTestId("global-chat-reply-preview");
    await expect(preview).toContainText("Antwort an Lola Lernende");
    await expect(preview).toContainText(text);
    await expect(page.getByTestId("global-chat-input")).toBeFocused();
    await preview.getByTestId("global-chat-reply-cancel").click();
    await expect(preview).toHaveCount(0);

    // Escape cancels the reply first, the chat stays open
    await original.hover();
    await original.getByTestId("global-chat-reply").click();
    await page.keyboard.press("Escape");
    await expect(preview).toHaveCount(0);
    await expect(page.getByTestId("global-chat-panel")).toBeVisible();

    // keyboard only: Tab to the button, Enter
    await original.getByTestId("global-chat-reply").focus();
    await page.keyboard.press("Enter");
    await expect(preview).toBeVisible();
    const answer = `Ich komme! 🎉 ${Date.now()}`;
    await page.getByTestId("global-chat-input").fill(answer);
    await page.getByTestId("global-chat-input").press("Enter");
    const reply = page.getByTestId("global-chat-message").filter({ hasText: answer });
    await expect(reply.getByTestId("global-chat-reply-quote")).toContainText(text);
    await expect(preview).toHaveCount(0);

    // the quote jumps to the original and highlights it
    await page.getByTestId("global-chat-list").evaluate((el) => { el.scrollTop = el.scrollHeight; });
    await reply.getByTestId("global-chat-reply-quote").click();
    await expect(original).toHaveAttribute("data-highlighted", "true");
    await expect(original).toBeInViewport();
  });

  test("the original is deleted: the reply stays and says so", async ({ page }) => {
    const other = await apiToken(STUDENT2);
    const text = `Tippfehler ${Date.now()}`;
    const original = await (await apiPost(other, text)).json();
    const mine = await apiToken(STUDENT1);
    const answer = `Was meinst du? ${Date.now()}`;
    expect((await apiPost(mine, answer, original.id)).status).toBe(201);
    await openChat(page);
    const reply = page.getByTestId("global-chat-message").filter({ hasText: answer });
    await expect(reply.getByTestId("global-chat-reply-quote")).toHaveAttribute("data-available", "true");
    const del = await fetch(`${API_URL}/api/v1/global-chat/messages/${original.id}`, { method: "DELETE", headers: { Authorization: `Bearer ${other}` } });
    expect(del.status).toBe(204);
    // polling removes the original and turns the quote into the fallback, no error
    await expect(messageWith(page, text)).toHaveCount(0, { timeout: 15_000 });
    await expect(reply.getByTestId("global-chat-reply-quote")).toHaveAttribute("data-available", "false");
    await expect(reply.getByTestId("global-chat-reply-quote")).toContainText("nicht mehr verfügbar");
  });

  test("mobile: swipe left replies, a vertical drag scrolls, the button is visible without hover", async ({ page, isMobile }) => {
    test.skip(!isMobile, "touch gestures run in the mobile project");
    const other = await apiToken(STUDENT2);
    const text = `Swipe mich ${Date.now()}`;
    expect((await apiPost(other, text)).status).toBe(201);
    await openChat(page);
    const message = messageWith(page, text);
    const bubble = message.getByTestId("global-chat-swipe");
    await expect(bubble).toBeVisible();
    // the list keeps native vertical scrolling on the message
    expect(await bubble.evaluate((el) => getComputedStyle(el).touchAction)).toBe("pan-y");
    // touch screens show the Reply button without hover
    expect(await message.getByTestId("global-chat-reply").evaluate((el) => getComputedStyle(el).opacity)).toBe("1");

    await swipe(bubble, -10, 70); // vertical: scrolling, not a reply
    await expect(page.getByTestId("global-chat-reply-preview")).toHaveCount(0);
    await swipe(bubble, 90, 0); // rightward: never a reply
    await expect(page.getByTestId("global-chat-reply-preview")).toHaveCount(0);
    await swipe(bubble, -40, 0); // too short
    await expect(page.getByTestId("global-chat-reply-preview")).toHaveCount(0);

    await swipe(bubble, -90, 4);
    await expect(page.getByTestId("global-chat-reply-preview")).toContainText(text);
    await expect(page.getByTestId("global-chat-panel")).toBeVisible(); // the swipe did not close the chat
    const answer = `per Swipe ${Date.now()}`;
    await page.getByTestId("global-chat-input").fill(answer);
    await page.getByTestId("global-chat-send").click();
    await expect(page.getByTestId("global-chat-message").filter({ hasText: answer }).getByTestId("global-chat-reply-quote")).toContainText(text);
    // nothing scrolls sideways on a phone
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  });
});
