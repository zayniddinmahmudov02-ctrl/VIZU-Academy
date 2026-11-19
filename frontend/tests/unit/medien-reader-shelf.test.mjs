import assert from "node:assert/strict";
import { test } from "node:test";

import {
  clampView, dragAngle, FLIP_DEG, fitPage, MAX_SCALE, nextZoomStep, pinchView, swipeDecision, tapZone, zoomAt,
} from "../../src/features/medien/lib/reader-gestures.ts";
import { groupByCategory, rowsOf, shelfColumns } from "../../src/features/medien/lib/shelf.ts";
import {
  formatCueTime, initialSubtitle, normalizePrefs, parseCueTime, stateFromSwitches, subtitleLines, switchesOf,
} from "../../src/features/medien/lib/subtitles.ts";

// ---------------- book reader ----------------

test("a page fits the stage in its own proportions", () => {
  assert.deepEqual(fitPage(400, 800, 0.7, 10), { w: 380, h: 543 }); // phone: the width decides
  assert.deepEqual(fitPage(1400, 800, 0.7, 10), { w: 546, h: 780 }); // desktop: the height decides
});

test("a zoomed page can be moved only as far as it covers the stage; an un-zoomed page stays centred", () => {
  assert.deepEqual(clampView({ scale: 1, x: 50, y: -30 }, 380, 543, 400, 600), { scale: 1, x: 0, y: 0 });
  const v = clampView({ scale: 2, x: 999, y: -999 }, 380, 543, 400, 600);
  assert.deepEqual(v, { scale: 2, x: 180, y: -243 });
  assert.equal(clampView({ scale: 9, x: 0, y: 0 }, 100, 100, 100, 100).scale, MAX_SCALE);
});

test("pinch: the point under the fingers stays under them", () => {
  const start = { scale: 1, x: 0, y: 0 };
  const v = pinchView(start, { x: 90, y: 0 }, { x: 110, y: 0 }, { x: 80, y: 0 }, { x: 120, y: 0 }); // fingers spread 2× around x = 100
  assert.equal(v.scale, 2);
  assert.equal(v.x, -100); // the page point at 100 is now at (100 - (-100)) / 2 = 100 → still under the fingers
  assert.equal(pinchView(start, { x: 0, y: 0 }, { x: 100, y: 0 }, { x: 0, y: 0 }, { x: 10, y: 0 }).scale, 1); // never smaller than the page
  const z = zoomAt({ scale: 1, x: 0, y: 0 }, 2, { x: 50, y: 20 });
  assert.deepEqual(z, { scale: 2, x: -50, y: -20 });
  assert.equal(nextZoomStep(1, 1), 1.25);
  assert.equal(nextZoomStep(1.25, -1), 1);
  assert.equal(nextZoomStep(4, 1), 4);
});

test("swipe right-to-left = next page, left-to-right = previous; short, slow or vertical = nothing", () => {
  assert.equal(swipeDecision(-120, 10, 400, 400), "next");
  assert.equal(swipeDecision(120, 5, 400, 400), "prev");
  assert.equal(swipeDecision(-50, 0, 60, 400), "next"); // a quick flick
  assert.equal(swipeDecision(-50, 0, 600, 400), "cancel"); // short and slow
  assert.equal(swipeDecision(-100, 140, 300, 400), "cancel"); // mostly vertical
  assert.equal(swipeDecision(-10, 0, 20, 400), "cancel");
});

test("click zones and the turning angle", () => {
  assert.equal(tapZone(30, 900), "prev");
  assert.equal(tapZone(450, 900), "middle");
  assert.equal(tapZone(800, 900), "next");
  assert.equal(dragAngle(0, 400, "next"), -0);
  assert.equal(dragAngle(-320, 400, "next"), -FLIP_DEG);
  assert.equal(dragAngle(0, 400, "prev"), -FLIP_DEG);
  assert.equal(dragAngle(320, 400, "prev"), -0);
});

// ---------------- bookshelf ----------------

test("books per board follow the width, covers never get too small", () => {
  assert.equal(shelfColumns(328), 3); // 360 px phone
  assert.equal(shelfColumns(250), 2);
  assert.equal(shelfColumns(720), 5);
  assert.equal(shelfColumns(1200), 8);
  assert.equal(shelfColumns(0), 3);
  assert.deepEqual(rowsOf([1, 2, 3, 4, 5, 6, 7], 3), [[1, 2, 3], [4, 5, 6], [7]]);
});

test("one shelf per category in the admin's order, books without one last", () => {
  const cats = [{ id: "a", name: "Literatur", slug: "literatur" }, { id: "b", name: "Grammatik", slug: "grammatik" }, { id: "c", name: "Wortschatz", slug: "wortschatz" }];
  const books = [
    { id: 1, category: cats[1] }, { id: 2, category: null }, { id: 3, category: cats[0] }, { id: 4, category: cats[1] }, { id: 5, category: { id: "x", name: "?", slug: "x" } },
  ];
  const groups = groupByCategory(books, cats, "Weitere Bücher");
  assert.deepEqual(groups.map((g) => [g.name, g.books.map((b) => b.id)]), [["Literatur", [3]], ["Grammatik", [1, 4]], ["Weitere Bücher", [2, 5]]]);
});

// ---------------- subtitles: editor times, original language, the two switches ----------------

test("cue times for the editor", () => {
  assert.equal(formatCueTime(62_250), "1:02.250");
  assert.equal(formatCueTime(3_723_004), "1:02:03.004");
  assert.equal(parseCueTime("1:02.25"), 62_250);
  assert.equal(parseCueTime("01:02:03,004"), 3_723_004);
  assert.equal(parseCueTime("12.5"), 12_500);
  assert.equal(parseCueTime(formatCueTime(5_999)), 5_999);
  for (const bad of ["", "abc", "1:75", "1:2:3:4", "-1"]) assert.equal(parseCueTime(bad), null);
});

test("the film's original language is on top in the dual view and starts first", () => {
  assert.deepEqual(subtitleLines(["de", "en", "uz"], "uz", true, "en", "en"), ["en", "uz"]);
  assert.deepEqual(subtitleLines(["de", "uz"], "uz", true, "de"), ["de", "uz"]); // default original = German
  const prefs = normalizePrefs(null);
  assert.equal(initialSubtitle(["de", "en", "uz"], null, prefs, "en"), "en");
  assert.equal(initialSubtitle(["de", "uz"], null, prefs, "en"), "de");
});

test("Original / Translation switches map to the player state and back", () => {
  const all = ["de", "uz", "en"];
  assert.deepEqual(switchesOf(all, "de", "de", true, "uz"), { showOriginal: true, showTranslation: true, translation: "uz" });
  assert.deepEqual(switchesOf(all, "de", "de", false, "uz"), { showOriginal: true, showTranslation: false, translation: "uz" });
  assert.deepEqual(switchesOf(all, "de", "en", false, null), { showOriginal: false, showTranslation: true, translation: "en" });
  assert.deepEqual(switchesOf(all, "de", "off", false, "en"), { showOriginal: false, showTranslation: false, translation: "en" });
  assert.deepEqual(stateFromSwitches(all, "de", { showOriginal: true, showTranslation: true, translation: "uz" }), { subtitle: "de", dual: true, secondary: "uz" });
  assert.deepEqual(stateFromSwitches(all, "de", { showOriginal: false, showTranslation: true, translation: "uz" }), { subtitle: "uz", dual: false, secondary: "uz" });
  assert.deepEqual(stateFromSwitches(all, "de", { showOriginal: true, showTranslation: false, translation: "uz" }), { subtitle: "de", dual: false, secondary: "uz" });
  assert.deepEqual(stateFromSwitches(all, "de", { showOriginal: false, showTranslation: false, translation: "uz" }), { subtitle: "off", dual: false, secondary: "uz" });
  // a film without its original track: only the translation can be switched
  assert.deepEqual(stateFromSwitches(["uz"], "de", { showOriginal: true, showTranslation: false, translation: "uz" }), { subtitle: "off", dual: false, secondary: "uz" });
  // round trip of every state
  for (const st of [{ subtitle: "de", dual: true, secondary: "en" }, { subtitle: "de", dual: false, secondary: "en" }, { subtitle: "en", dual: false, secondary: "en" }]) {
    assert.deepEqual(stateFromSwitches(all, "de", switchesOf(all, "de", st.subtitle, st.dual, st.secondary)), st);
  }
});
