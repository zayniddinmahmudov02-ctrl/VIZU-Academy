// node --test tests/unit  (Node >= 22.18 runs the .ts module directly)
import assert from "node:assert/strict";
import { test } from "node:test";

import { decideBack, EXIT_WINDOW_MS, homeOf, isStartPage } from "../../src/features/mobile-app/utils/back-button.ts";

const at = (path, extra = {}) => decideBack({ dialogOpen: false, path, canGoBack: true, now: 10_000, lastHintAt: null, ...extra });

test("an open dialog closes first, wherever it is", () => {
  assert.equal(at("/dashboard", { dialogOpen: true }), "close-dialog");
  assert.equal(at("/medien/musik", { dialogOpen: true }), "close-dialog");
});

test("inner pages go back; without history to their panel's start page", () => {
  assert.equal(at("/medien/bibliothek/abc"), "history-back");
  assert.equal(at("/teacher/kontroll/x", { canGoBack: false }), "home");
  assert.equal(homeOf("/teacher/kontroll/x"), "/teacher");
  assert.equal(homeOf("/admin/team"), "/admin");
  assert.equal(homeOf("/lektion/1"), "/dashboard");
});

test("a start page needs a second press within the window to close the app", () => {
  for (const p of ["/dashboard", "/teacher", "/admin", "/login", "/", "/dashboard/"]) assert.equal(isStartPage(p), true, p);
  assert.equal(isStartPage("/dashboard/x"), false);
  assert.equal(at("/dashboard"), "exit-hint");
  assert.equal(at("/dashboard", { lastHintAt: 10_000 - 500 }), "exit");
  assert.equal(at("/dashboard", { lastHintAt: 10_000 - EXIT_WINDOW_MS - 1 }), "exit-hint");
  assert.equal(at("/teacher?x=1", { lastHintAt: 9_000 }), "exit");
});
