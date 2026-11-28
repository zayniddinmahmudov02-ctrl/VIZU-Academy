// node --test tests/unit  (Node >= 22.18 runs the .ts module directly)
import assert from "node:assert/strict";
import { test } from "node:test";

import { accessDate, levelStatus, renewHref, STATUS_TONE } from "../../src/features/lms/level-status.ts";

const sale = (over = {}) => ({
  available: true, coming_soon: false, sales_enabled: true, sales_closed: false, owned: false,
  access_until: null, expired_at: null, free_lessons: 1, offer: null, packages: [], ...over,
});

test("course card state comes only from the backend sale block", () => {
  assert.equal(levelStatus({}), "ACTIVE"); // staff / no sale info
  assert.equal(levelStatus({ sale: sale({ coming_soon: true, available: false }) }), "COMING_SOON");
  assert.equal(levelStatus({ sale: sale({ owned: true, access_until: "2026-12-20T10:00:00Z" }) }), "ACTIVE");
  assert.equal(levelStatus({ sale: sale() }), "PURCHASE_REQUIRED");
  assert.equal(levelStatus({ sale: sale({ sales_enabled: false, sales_closed: true }) }), "LOCKED");
});

test("an expired purchase says so instead of the plain buy prompt", () => {
  assert.equal(levelStatus({ sale: sale({ expired_at: "2026-11-27T19:00:00Z" }) }), "EXPIRED");
  // owned wins (a renewal is active), coming soon wins (nothing to renew yet)
  assert.equal(levelStatus({ sale: sale({ owned: true, expired_at: "2026-11-27T19:00:00Z" }) }), "ACTIVE");
  assert.equal(levelStatus({ sale: sale({ coming_soon: true, expired_at: "2026-11-27T19:00:00Z" }) }), "COMING_SOON");
  assert.ok(STATUS_TONE.EXPIRED.includes("amber"));
});

test("access dates are shown on the Tashkent calendar", () => {
  assert.equal(accessDate("2026-11-27T19:00:00Z"), "28.11.2026"); // 00:00 in Tashkent (UTC+5)
  assert.equal(accessDate("2026-11-27T18:59:00Z"), "27.11.2026");
  assert.equal(accessDate(null), "");
  assert.equal(accessDate(undefined), "");
  assert.equal(accessDate("not a date"), "");
});

test("renew leads to the level's own offer when it is on sale", () => {
  const offer = { code: "A1", kind: "LEVEL", purchasable: true };
  assert.equal(renewHref(sale({ offer })), "/angebote?offer=A1");
  assert.equal(renewHref(sale({ offer: { ...offer, code: "A1 B1" } })), "/angebote?offer=A1%20B1");
  assert.equal(renewHref(sale({ offer: { ...offer, purchasable: false } })), "/angebote");
  assert.equal(renewHref(sale()), "/angebote");
  assert.equal(renewHref(undefined), "/angebote");
});
