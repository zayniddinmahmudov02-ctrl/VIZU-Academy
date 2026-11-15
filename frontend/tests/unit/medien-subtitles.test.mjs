import assert from "node:assert/strict";
import { test } from "node:test";

import {
  activeCues, cleanWord, cueKey, DEFAULT_PREFS, initialSubtitle, normalizePrefs, pickSecondary, sortByLanguage, stateOf, subtitleLines, subtitleStyle, tokenize,
} from "../../src/features/medien/lib/subtitles.ts";

const cues = [[500, 3000, "Guten Tag"], [3500, 5500, "Auf Wiedersehen"], [5000, 7000, "Überlappung"], [9000, 9500, "Ende"]];

test("the cue at a time: start inclusive, end exclusive, nothing in the gaps", () => {
  assert.deepEqual(activeCues(cues, 0), []);
  assert.deepEqual(activeCues(cues, 500).map((c) => c[2]), ["Guten Tag"]);
  assert.deepEqual(activeCues(cues, 2999).map((c) => c[2]), ["Guten Tag"]);
  assert.deepEqual(activeCues(cues, 3000), []);
  assert.deepEqual(activeCues(cues, 3499), []);
  assert.deepEqual(activeCues(cues, 9499).map((c) => c[2]), ["Ende"]);
  assert.deepEqual(activeCues(cues, 9500), []);
  assert.deepEqual(activeCues([], 10), []);
});

test("overlapping cues are all shown, in start order; seeking back and forth gives the same answer", () => {
  assert.deepEqual(activeCues(cues, 5200).map((c) => c[2]), ["Auf Wiedersehen", "Überlappung"]);
  assert.deepEqual(activeCues(cues, 6000).map((c) => c[2]), ["Überlappung"]);
  for (const ms of [8000, 600, 5200, 0, 9100, 5200]) assert.equal(cueKey(activeCues(cues, ms)), cueKey(activeCues(cues, ms)));
  assert.equal(cueKey(activeCues(cues, 600)), "500");
  assert.equal(cueKey(activeCues(cues, 8000)), "");
});

test("lookup is exact on a long list (speed does not matter: the time comes from the video)", () => {
  const long = Array.from({ length: 5000 }, (_, i) => [i * 1000, i * 1000 + 800, `Zeile ${i}`]);
  for (const i of [0, 1, 2499, 4999]) assert.deepEqual(activeCues(long, i * 1000 + 400).map((c) => c[2]), [`Zeile ${i}`]);
  assert.deepEqual(activeCues(long, 2499 * 1000 + 900), []);
});

test("words: punctuation and quotes are cut off, inner apostrophes and hyphens stay", () => {
  assert.equal(cleanWord("Welt!"), "Welt");
  assert.equal(cleanWord("„Hallo“,"), "Hallo");
  assert.equal(cleanWord("(Köln)"), "Köln");
  assert.equal(cleanWord("o‘zbekcha"), "o'zbekcha");
  assert.equal(cleanWord("Tag-und-Nacht."), "Tag-und-Nacht");
  assert.equal(cleanWord("..."), "");
  assert.deepEqual(tokenize("Ich lerne, jeden Tag!").map((t) => t.word), ["Ich", null, "lerne", null, "jeden", null, "Tag"]);
  assert.deepEqual(tokenize("— 12 €").filter((t) => t.word).map((t) => t.word), ["12"]);
  assert.equal(tokenize("Ich lerne, jeden Tag!").map((t) => t.text).join(""), "Ich lerne, jeden Tag!");
  assert.deepEqual(tokenize(""), []);
});

test("settings: missing or invalid values fall back to the defaults", () => {
  assert.deepEqual(normalizePrefs(null), DEFAULT_PREFS);
  assert.deepEqual(normalizePrefs({ size: "huge", color: "red", bg_opacity: 300, position: "top", font: "comic", secondary: "xx", dual: "yes" }), DEFAULT_PREFS);
  const mine = { enabled: false, size: "large", color: "#ffe066", bg_opacity: 40, position: "higher", font: "serif", dual: true, secondary: "en" };
  assert.deepEqual(normalizePrefs(mine), mine);
});

test("which subtitle starts: last used on this film, else the default (German first), else off", () => {
  const prefs = DEFAULT_PREFS;
  assert.equal(initialSubtitle(["de", "uz"], null, prefs), "de");
  assert.equal(initialSubtitle(["uz", "en"], null, prefs), "uz");
  assert.equal(initialSubtitle(["de", "uz"], { subtitle: "uz" }, prefs), "uz");
  assert.equal(initialSubtitle(["de", "uz"], { subtitle: "off" }, prefs), "off");
  assert.equal(initialSubtitle(["de"], { subtitle: "en" }, prefs), "de");            // that language no longer exists
  assert.equal(initialSubtitle(["de", "uz"], null, { ...prefs, enabled: false }), "off");
  assert.equal(initialSubtitle([], null, prefs), "off");
});

test("dual subtitles: German on top, only with two tracks, the wanted second language when it exists", () => {
  assert.deepEqual(subtitleLines(["de", "uz"], "de", true, "uz"), ["de", "uz"]);
  assert.deepEqual(subtitleLines(["de", "uz"], "uz", true, "de"), ["de", "uz"]);      // German is moved to the top
  assert.deepEqual(subtitleLines(["de", "uz", "en"], "de", true, "en"), ["de", "en"]);
  assert.deepEqual(subtitleLines(["de", "uz", "en"], "de", true, "ru"), ["de", "uz"]); // wanted language missing -> a sensible other one
  assert.deepEqual(subtitleLines(["uz", "en"], "uz", true, "en"), ["uz", "en"]);      // no German: the chosen order
  assert.deepEqual(subtitleLines(["de"], "de", true, "uz"), ["de"]);                   // one track: dual is impossible
  assert.deepEqual(subtitleLines(["de", "uz"], "de", false, "uz"), ["de"]);
  assert.deepEqual(subtitleLines(["de", "uz"], "off", true, "uz"), []);
  assert.deepEqual(subtitleLines(["de", "uz"], "en", false, "uz"), []);                // chosen language not available
  assert.equal(pickSecondary(["de"], "de", "uz"), null);
  assert.equal(pickSecondary(["de", "uz"], "de", "de"), "uz");
});

test("appearance maps to CSS; the text sits above the control bar, 'higher' lifts it more", () => {
  const s = subtitleStyle({ ...DEFAULT_PREFS, size: "large", color: "#7dd3fc", bg_opacity: 40, font: "mono" }, 90);
  assert.equal(s.block.color, "#7dd3fc");
  assert.match(s.block.fontFamily, /mono/i);
  assert.equal(s.line.backgroundColor, "rgba(0, 0, 0, 0.4)");
  assert.equal(subtitleStyle(DEFAULT_PREFS, 0).block.bottom, "1.25rem");                       // bar hidden
  assert.equal(subtitleStyle(DEFAULT_PREFS, 96).block.bottom, "calc(96px + 0.75rem)");        // bar shown: always above it (one or two rows)
  assert.equal(subtitleStyle(DEFAULT_PREFS, 150.4).block.bottom, "calc(150px + 0.75rem)");
  assert.equal(subtitleStyle({ ...DEFAULT_PREFS, position: "higher" }, 0).block.bottom, "4.75rem");
  assert.equal(subtitleStyle({ ...DEFAULT_PREFS, position: "higher" }, 96).block.bottom, "calc(96px + 4.25rem)");
  assert.equal(subtitleStyle({ ...DEFAULT_PREFS, bg_opacity: 0 }, 96).line.backgroundColor, "rgba(0, 0, 0, 0)");
});

test("languages are offered as Deutsch, Uzbek, English", () => {
  const subs = [{ language: "uz" }, { language: "en" }, { language: "de" }, { language: "ru" }, { language: "fr" }];
  assert.deepEqual(sortByLanguage(subs).map((s) => s.language), ["de", "uz", "en", "ru", "fr"]);
  assert.deepEqual(sortByLanguage([{ language: "en" }, { language: "de" }]).map((s) => s.language), ["de", "en"]);
  assert.deepEqual(subs.map((s) => s.language), ["uz", "en", "de", "ru", "fr"]); // the input is not changed
});

test("the state stored per film", () => {
  assert.deepEqual(stateOf({ subtitle: "de", dual: true, secondary: "uz", speed: 1.5, quality: "720p" }), { subtitle: "de", dual: true, speed: 1.5, secondary: "uz", quality: "720p" });
  assert.deepEqual(stateOf({ subtitle: "off", dual: false, secondary: null, speed: 1, quality: null }), { subtitle: "off", dual: false, speed: 1 });
});
