// node --test tests/unit  (Node >= 22.18 runs the .ts module directly)
import assert from "node:assert/strict";
import { test } from "node:test";

import { CHAT_PAGES, chatVisibleOn } from "../../src/features/global-chat/chat-visibility.ts";

test("the Global Chat button is shown only on the dashboard home pages", () => {
  assert.deepEqual([...CHAT_PAGES], ["/dashboard", "/teacher", "/admin"]);
  for (const p of ["/dashboard", "/dashboard/", "/teacher", "/admin", "/admin/"]) assert.equal(chatVisibleOn(p), true, p);
});

test("every other page has no chat button", () => {
  for (const p of ["/kurse", "/lektion/1", "/medien", "/medien/musik", "/vorbereitung/multilevel", "/profil", "/dashboard/settings",
    "/teacher/groups", "/admin/users", "/admin/global-chat", "/", "/login", "/dashboards", "", null, undefined]) {
    assert.equal(chatVisibleOn(p), false, String(p));
  }
});
